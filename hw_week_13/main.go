package main

import (
	"bufio"
	"compress/gzip"
	"errors"
	"flag"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	sync "sync"
	"time"

	"github.com/bradfitz/gomemcache/memcache"
)

const (
	normalErrRate          float64 = 0.01
	tasksChannelBufferSize int     = 1000
	goroutinesNum          int     = 6
)

// AppsInstalled ...
type AppsInstalled struct {
	DevType string
	DevId   string
	Lat     float64
	Lon     float64
	Apps    []uint32
}

// ProcessResultReport ...
type ProcessResultReport struct {
	numProcessed int
	numErrors    int
}

// DotRename ...
func DotRename(path string) error {

	head, fileName := filepath.Split(path)
	newPath := filepath.Join(head, "."+fileName)

	if err := os.Rename(path, newPath); err != nil {
		log.Printf("Failed to rename path %s to %s", path, newPath)
		return err
	}

	return nil
}

// SerializeInstalledApps ...
func SerializeInstalleApps(ai *AppsInstalled) (string, string) {

	userApps := &UserApps{}
	userApps.Lat = ai.Lat
	userApps.Lon = ai.Lon
	key := strings.Join([]string{ai.DevType, ai.DevId}, ":")
	userApps.Apps = append(userApps.Apps, ai.Apps...)
	packedUserApps := userApps.String()

	return key, packedUserApps
}

// ParseAppsInstalled ...
func ParseAppsInstalled(line string) (*AppsInstalled, error) {

	strippedLine := strings.Trim(line, " ")
	lineParts := strings.Split(strippedLine, "\t")

	if len(lineParts) < 5 {
		return nil, errors.New("Defect line")
	}

	devType := lineParts[0]
	devId := lineParts[1]
	lat := lineParts[2]
	lon := lineParts[3]
	rawApps := lineParts[4]

	if devType == "" || devId == "" {
		return nil, errors.New("Haven't found dev type or dev id")
	}

	apps := make([]uint32, 0)
	rawAppsSplitted := strings.Split(rawApps, ",")

	for _, app := range rawAppsSplitted {
		appStripped := strings.Trim(app, " ")
		appAsNum, err := strconv.Atoi(appStripped)
		if err != nil {
			log.Printf("Not all user apps are digits %s", line)
			continue
		}
		apps = append(apps, uint32(appAsNum))
	}

	latAsFloat, err := strconv.ParseFloat(lat, 64)
	if err != nil {
		log.Printf("Invalid latitude coords: '%s'", line)
		return nil, err
	}

	lonAsFloat, err := strconv.ParseFloat(lon, 64)
	if err != nil {
		log.Printf("Invalid longitude coords: '%s'", line)
		return nil, err
	}

	appsInstalled := &AppsInstalled{
		DevType: devType,
		DevId:   devId,
		Lat:     latAsFloat,
		Lon:     lonAsFloat,
		Apps:    apps,
	}

	return appsInstalled, nil
}

func UploadToMemcache(
	client *memcache.Client,
	uploadChan <-chan map[string]string,
	resultChan chan<- ProcessResultReport,
	retriesLimit int,
	wg *sync.WaitGroup,
) {

	defer wg.Done()
	totalNumErrors, totalNumProcessed := 0, 0

	for taskUpload := range uploadChan {
		success := true

		for numAttempt := 0; numAttempt < retriesLimit; numAttempt++ {

			for uploadKey, uploadValue := range taskUpload {
				if err := client.Set(&memcache.Item{
					Key:   uploadKey,
					Value: []byte(uploadValue),
				}); err != nil {
					success = false
				}
			}

			if success {
				break
			}

		}

		numErrors := 0
		numProcessed := 1
		if !success {
			numErrors = 1
			numProcessed = 0
		}

		totalNumErrors += numErrors
		totalNumProcessed += numProcessed
	}

	resultChan <- ProcessResultReport{
		numErrors:    totalNumErrors,
		numProcessed: totalNumProcessed,
	}
}

func HandleSingleFile(fileName string, clients map[string]*memcache.Client, retriesLimit int) {

	uploadingChans := make(map[string]chan map[string]string)
	for devType := range clients {
		uploadingChans[devType] = make(chan map[string]string, tasksChannelBufferSize)
	}

	processResultChan := make(chan ProcessResultReport, tasksChannelBufferSize)
	wg := &sync.WaitGroup{}
	for devType, client := range clients {
		wg.Add(1)
		go UploadToMemcache(client, uploadingChans[devType], processResultChan, retriesLimit, wg)
	}

	file, err := os.Open(fileName)

	if err != nil {
		log.Printf("Error during file open %s", fileName)
		return
	}
	defer file.Close()

	gz, err := gzip.NewReader(file)
	if err != nil {
		log.Printf("Error during reading archive file %s", fileName)
		return
	}
	defer gz.Close()

	scanner := bufio.NewScanner(gz)
	numProcessed, numErrors := 0, 0

	for scanner.Scan() {
		line := scanner.Text()
		lineStripped := strings.Trim(line, " ")

		if lineStripped == "" {
			continue
		}

		appsInstalled, err := ParseAppsInstalled(lineStripped)
		if err != nil {
			log.Printf("Error occured while parsing file")
			numErrors++
			continue
		}

		_, ok := clients[appsInstalled.DevType]
		if !ok {
			log.Printf("Unknown device type %s", appsInstalled.DevType)
			numErrors++
			continue
		}

		key, packedUserApps := SerializeInstalleApps(appsInstalled)
		uploadingChans[appsInstalled.DevType] <- map[string]string{
			key: packedUserApps,
		}
	}

	for _, uploadingChan := range uploadingChans {
		close(uploadingChan)
	}

	numReceivedReports := 0
	for processResultReport := range processResultChan {
		numProcessed += processResultReport.numProcessed
		numErrors += processResultReport.numErrors
		numReceivedReports++
		if numReceivedReports == len(uploadingChans) {
			break
		}
	}

	errRate := 1.0
	if numProcessed != 0 {
		errRate = float64(numErrors) / float64(numProcessed)
	}

	if errRate < normalErrRate {
		log.Printf("Acceptable error rate (%f). Successfully load.", errRate)
	} else {
		log.Printf("High error rate (%f > %f). Failed load.", errRate, normalErrRate)
	}

	wg.Wait()
}

// HandleFiles ...
func HandleFiles(taskChan <-chan string, clients map[string]*memcache.Client, retriesLimit int, wg *sync.WaitGroup) {

	defer wg.Done()
	for fileName := range taskChan {
		HandleSingleFile(fileName, clients, retriesLimit)
	}

}

func minWorkersNum(patternMatchesNum, goroutinesNum int) int {

	if patternMatchesNum < goroutinesNum {
		return patternMatchesNum
	}

	return goroutinesNum
}

func main() {

	var idfa string
	var gaid string
	var adid string
	var dvid string
	var pattern string
	var storageTimeout int
	var storageMaxRetries int

	flag.StringVar(&idfa, "idfa", "127.0.0.1:33013", "idfa dev type")
	flag.StringVar(&gaid, "gaid", "127.0.0.1:33014", "gaid dev type")
	flag.StringVar(&adid, "adid", "127.0.0.1:33015", "adid dev type")
	flag.StringVar(&dvid, "dvid", "127.0.0.1:33016", "dvid dev type")
	flag.StringVar(&pattern, "pattern", "./*.tsv.gz", "pattern for parsing file")
	flag.IntVar(&storageTimeout, "--storage-timeout", 3, "Timeout for storage connection in seconds")
	flag.IntVar(&storageMaxRetries, "--storage-max-retries", 3, "Maximum retries number in case of failed saving")

	flag.Parse()

	memcachedAddresses := map[string]string{
		"idfa": idfa,
		"gaid": gaid,
		"adid": adid,
		"dvid": dvid,
	}
	memcachedClients := make(map[string]*memcache.Client)
	for devType, address := range memcachedAddresses {
		memcacheClient := memcache.New(address)
		memcacheClient.Timeout = time.Duration(storageTimeout) * time.Second
		memcachedClients[devType] = memcacheClient
	}

	patternMatches, err := filepath.Glob(pattern)
	if err != nil {
		log.Fatal("Something went wrong during parsing pattern")
	}

	workersNumber := minWorkersNum(len(patternMatches), goroutinesNum)
	log.Printf("File number is %d, workers number is %d", len(patternMatches), workersNumber)
	taskFileNameInput := make(chan string, tasksChannelBufferSize)

	wg := &sync.WaitGroup{}
	for workerNum := 0; workerNum < workersNumber; workerNum++ {
		wg.Add(1)
		go HandleFiles(taskFileNameInput, memcachedClients, storageMaxRetries, wg)
	}

	for _, matchedFileName := range patternMatches {
		taskFileNameInput <- matchedFileName
	}
	close(taskFileNameInput)
	wg.Wait()

	for _, matchedFileName := range patternMatches {
		err := DotRename(matchedFileName)
		if err != nil {
			log.Printf("Error during dotting file %s", matchedFileName)
		}
	}
}
