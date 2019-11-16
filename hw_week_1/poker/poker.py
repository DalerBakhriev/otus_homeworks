#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -----------------
# Реализуйте функцию best_hand, которая принимает на вход
# покерную "руку" (hand) из 7ми карт и возвращает лучшую
# (относительно значения, возвращаемого hand_rank)
# "руку" из 5ти карт. У каждой карты есть масть(suit) и
# ранг(rank)
# Масти: трефы(clubs, C), пики(spades, S), червы(hearts, H), бубны(diamonds, D)
# Ранги: 2, 3, 4, 5, 6, 7, 8, 9, 10 (ten, T), валет (jack, J), дама (queen, Q), король (king, K), туз (ace, A)
# Например: AS - туз пик (ace of spades), TH - дестяка черв (ten of hearts), 3C - тройка треф (three of clubs)

# Задание со *
# Реализуйте функцию best_wild_hand, которая принимает на вход
# покерную "руку" (hand) из 7ми карт и возвращает лучшую
# (относительно значения, возвращаемого hand_rank)
# "руку" из 5ти карт. Кроме прочего в данном варианте "рука"
# может включать джокера. Джокеры могут заменить карту любой
# масти и ранга того же цвета, в колоде два джокера.
# Черный джокер '?B' может быть использован в качестве треф
# или пик любого ранга, красный джокер '?R' - в качестве черв и бубен
# любого ранга.

# Одна функция уже реализована, сигнатуры и описания других даны.
# Вам наверняка пригодится itertools.
# Можно свободно определять свои функции и т.п.
# -----------------
from typing import Dict, List, Optional, Tuple, Union
from collections import Counter
import itertools as it

RANKS_MAPPINGS = {
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "T": 10,
    "J": 11,
    "Q": 12,
    "K": 13,
    "A": 14
}


def hand_rank(hand: Tuple[str]):

    """
    Возвращает значение определяющее ранг 'руки'
    """

    ranks = card_ranks(hand=hand, ranks_mappings=RANKS_MAPPINGS)
    if straight(ranks) and flush(hand):
        return 8, max(ranks)
    elif kind(4, ranks):
        return 7, kind(4, ranks), kind(1, ranks)
    elif kind(3, ranks) and kind(2, ranks):
        return 6, kind(3, ranks), kind(2, ranks)
    elif flush(hand):
        return 5, ranks
    elif straight(ranks):
        return 4, max(ranks)
    elif kind(3, ranks):
        return 3, kind(3, ranks), ranks
    elif two_pair(ranks):
        return 2, two_pair(ranks), ranks
    elif kind(2, ranks):
        return 1, kind(2, ranks), ranks
    else:
        return 0, ranks


def card_ranks(
        hand: Tuple[str],
        ranks_mappings: Dict[Union[int, str], int]
) -> List[int]:

    """
    Возвращает список рангов (его числовой эквивалент),
    отсортированный от большего к меньшему
    """

    ranks_numeric = sorted([ranks_mappings[card[0]] for card in hand])

    return ranks_numeric


def flush(hand: Tuple[str]) -> bool:

    """
    Возвращает True, если все карты одной масти
    """

    suits = set(map(lambda card: card[1], hand))

    return len(suits) == 1


def straight(ranks: List[int]) -> bool:

    """
    Возвращает True, если отсортированные ранги формируют последовательность 5ти,
    где у 5ти карт ранги идут по порядку (стрит)
    """

    for _, consecutive_ranks in it.groupby(
            enumerate(ranks),
            key=lambda x: x[1] - x[0]
    ):
        if len(tuple(consecutive_ranks)) == 5:
            return True

    return False


def get_all_ranks_with_n_freq(n: int, ranks: List[int]) -> Tuple[int]:

    """

    :param n:
    :param ranks:
    :return:
    """

    ranks_freq = Counter(ranks)
    ranks_with_n_freq = tuple(filter(lambda card: ranks_freq[card] == n, ranks_freq))

    return ranks_with_n_freq


def kind(n: int, ranks: List[int]) -> Optional[int]:

    """
    Возвращает первый ранг, который n раз встречается в данной руке.
    Возвращает None, если ничего не найдено
    """

    ranks_with_freq_n = get_all_ranks_with_n_freq(n=n, ranks=ranks)
    if not ranks_with_freq_n:
        return

    return sorted(ranks_with_freq_n)[0]


def two_pair(ranks: List[int]) -> Optional[Tuple[int, int]]:

    """
    Если есть две пары, то возвращает два соответствующих ранга,
    иначе возвращает None
    """

    ranks_with_freq_2 = get_all_ranks_with_n_freq(n=2, ranks=ranks)
    if len(ranks_with_freq_2) != 2:
        return

    return ranks_with_freq_2


def best_hand(hand: Tuple[str]):

    """
    Из "руки" в 7 карт возвращает лучшую "руку" в 5 карт
    """

    hands_ranks = dict()
    for poker_hand in it.combinations(hand, 5):
        hands_ranks[poker_hand] = hand_rank(poker_hand)

    return sorted(hands_ranks, key=lambda hand_: hands_ranks[hand_], reverse=True)[0]


def best_wild_hand(hand: Tuple[str]):

    """
    best_hand но с джокерами
    """

    return


def test_best_hand():
    print("test_best_hand...")
    assert (sorted(best_hand("6C 7C 8C 9C TC 5C JS".split()))
            == ['6C', '7C', '8C', '9C', 'TC'])
    assert (sorted(best_hand("TD TC TH 7C 7D 8C 8S".split()))
            == ['8C', '8S', 'TC', 'TD', 'TH'])
    assert (sorted(best_hand("JD TC TH 7C 7D 7S 7H".split()))
            == ['7C', '7D', '7H', '7S', 'JD'])
    print("OK")


def test_best_wild_hand():
    print("test_best_wild_hand...")
    assert (sorted(best_wild_hand("6C 7C 8C 9C TC 5C ?B".split()))
            == ['7C', '8C', '9C', 'JC', 'TC'])
    assert (sorted(best_wild_hand("TD TC 5H 5C 7C ?R ?B".split()))
            == ['7C', 'TC', 'TD', 'TH', 'TS'])
    assert (sorted(best_wild_hand("JD TC TH 7C 7D 7S 7H".split()))
            == ['7C', '7D', '7H', '7S', 'JD'])
    print("OK")


if __name__ == '__main__':
    test_best_hand()


