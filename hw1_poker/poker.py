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
# масти и ранга того же цвета, в колоде два джокерва.
# Черный джокер '?B' может быть использован в качестве треф
# или пик любого ранга, красный джокер '?R' - в качестве черв и бубен
# любого ранга.

# Одна функция уже реализована, сигнатуры и описания других даны.
# Вам наверняка пригодится itertoolsю
# Можно свободно определять свои функции и т.п.
# -----------------

from itertools import groupby, combinations


def ll(iterable):
    return len(list(iterable))


def all_equals(iterable):
    return ll(groupby(iterable)) == 1


def hand_rank(hand):
    """Возвращает значение определяющее ранг 'руки'"""
    ranks = card_ranks(hand)
    if straight(ranks) and flush(hand):
        return (8, max(ranks))
    elif kind(4, ranks):
        return (7, kind(4, ranks), kind(1, ranks))
    elif kind(3, ranks) and kind(2, ranks):
        return (6, kind(3, ranks), kind(2, ranks))
    elif flush(hand):
        return (5, ranks)
    elif straight(ranks):
        return (4, max(ranks))
    elif kind(3, ranks):
        return (3, kind(3, ranks), ranks)
    elif two_pair(ranks):
        return (2, two_pair(ranks), ranks)
    elif kind(2, ranks):
        return (1, kind(2, ranks), ranks)
    else:
        return (0, ranks)


def card_ranks(hand):
    """Возвращает список рангов (его числовой эквивалент),
    отсортированный от большего к меньшему"""
    total = '23456789TJQKA'
    return sorted([total.index(x[0]) for x in hand], reverse=True)


def flush(hand):
    """Возвращает True, если все карты одной масти"""
    groups = groupby(hand, lambda x: x[1])
    return ll(groups) == 1


def straight(ranks):
    """Возвращает True, если отсортированные ранги формируют последовательность 5ти,
    где у 5ти карт ранги идут по порядку (стрит)"""
    total = '.'.join([str(x) for x in reversed(range(2, 15))])
    return '.'.join([str(x) for x in ranks]) in total


def kind(n, ranks):
    """Возвращает первый ранг, который n раз встречается в данной руке.
    Возвращает None, если ничего не найдено"""
    for rank, group in groupby(ranks):
        if ll(group) == n:
            return rank


def two_pair(ranks):
    """Если есть две пары, то возврщает два соответствующих ранга,
    иначе возвращает None"""
    grouped = groupby(ranks)
    filtered = [rk for rk, gp in grouped if len(list(gp)) == 2]
    result = filtered[:2] if len(filtered) > 1 else None
    return result


def is_better_rank(a, b):
    is_better = False
    for x, y in zip(a, b):
        if x == y:
            continue
        is_better = x > y
    return is_better


def best_hand(hand):
    """Из "руки" в 7 карт возвращает лучшую "руку" в 5 карт """
    bhand = hand[:5]
    brank = hand_rank(bhand)

    for cur_hand in combinations(hand, 5):
        cur_rank = hand_rank(cur_hand)
        if is_better_rank(cur_rank, brank):
            brank = cur_rank
            bhand = cur_hand

    return bhand


def color(kind):
    if kind == 'C' or kind == 'S':
        return 'B'
    return 'R'


def wild_street(hand):
    pass


def wild_n(n, ranks, j_count):
    n = n - j_count
    for rank, group in groupby(ranks):
        if ll(group) >= n:
            return rank


def wild_flush(hand, jokers):
    groups = groupby(hand, lambda x: x[1])
    return ll(groups) == 1 and len(jokers) == 1 and color(hand[0][1]) == jokers[0][1]


def wild_full_house(ranks, hand, jokers):
    if len(jokers) == 2:
        kind(3,)

def best_wild_hand_one_joker(hand, j_color):
    bhand = None
    brank = None



    return None, None


def best_wild_hand_two_joker(hand):
    return None, None


def best_wild_hand(start_hand):
    jokers = [x for x in start_hand if '?' in x]
    hand = [x for x in start_hand if x not in jokers]

    bhand = best_hand(hand)
    brank = hand_rank(bhand)

    if len(jokers) == 0:
        return bhand

    for cur_hand in combinations(hand, 5):
        for joker in jokers:
            joker_bhand, jocker_brank = best_wild_hand_one_joker(cur_hand, joker)
            if is_better_rank(jocker_brank, brank):
                brank = jocker_brank
                bhand = joker_bhand

    if len(jokers) == 2:
        joker_bhand, jocker_brank = best_wild_hand_two_joker(hand)
        if is_better_rank(jocker_brank, brank):
            bhand = joker_bhand

    """best_hand но с джокерами"""
    return bhand


def test_best_hand():
    print("test_best_hand...")
    assert (sorted(best_hand("6C 7C 8C 9C TC 5C JS".split()))
            == ['6C', '7C', '8C', '9C', 'TC'])
    assert (sorted(best_hand("TD TC TH 7C 7D 8C 8S".split()))
            == ['8C', '8S', 'TC', 'TD', 'TH'])
    assert (sorted(best_hand("JD TC TH 7C 7D 7S 7H".split()))
            == ['7C', '7D', '7H', '7S', 'JD'])
    print('OK')


def test_best_wild_hand():
    print("test_best_wild_hand...")
    assert (sorted(best_wild_hand("6C 7C 8C 9C TC 5C ?B".split()))
            == ['7C', '8C', '9C', 'JC', 'TC'])
    assert (sorted(best_wild_hand("TD TC 5H 5C 7C ?R ?B".split()))
            == ['7C', 'TC', 'TD', 'TH', 'TS'])
    assert (sorted(best_wild_hand("JD TC TH 7C 7D 7S 7H".split()))
            == ['7C', '7D', '7H', '7S', 'JD'])
    print('OK')


if __name__ == '__main__':
    test_best_hand()
    test_best_wild_hand()
