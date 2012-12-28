from __future__ import division
import argparse
from copy import deepcopy
from bisect import bisect
from exp_to_level import exp_to_level
from fusion_factors import cost_factor, exp_factor, discount_factor
from textwrap import dedent
from collections import Counter
import pdb

class Card(object):
    """docstring for Card"""
    def __init__(self, rarity, level=None, exp=None, ato=None,
                 gained_exp=None, cost=None, acc_cost=0):
        super(Card, self).__init__()
        self.rarity     = rarity
        self.level      = level
        self.exp        = exp
        self.gained_exp = gained_exp
        self.cost       = cost
        self.acc_cost   = acc_cost

        if level is None and exp is not None:
            self.level = Card.calculate_level(exp)
        elif level is not None and exp is None:
            if ato is None:
                self.exp = Card.get_min_exp(level)
            else:
                self.exp = Card.get_exp_from_ato(level, ato)
        elif level is None and exp is None:
            self.level = 1
            self.exp = 0
        else:
            raise ValueError("Only one of level or exp must be set.")

    def fuse_with(self, fodder_list, ftype="weapon", rate=1):
        new_exp = self.exp
        acc_cost = self.acc_cost
        gained_exp = 0
        cost = 0
        for fodder in fodder_list:
            fodder_exp = 0
            cost += cost_factor[self.rarity]*self.level + \
                    cost_factor[fodder.rarity]*fodder.level
            acc_cost += fodder.acc_cost

            level_exp = exp_factor[(self.rarity, fodder.rarity)]
            if fodder.level == 1:
                fodder_exp = level_exp
            else:
                fodder_exp = level_exp*(fodder.level-1) + fodder.exp//100
            gained_exp += int(fodder_exp*rate)

        cost = cost*discount_factor[len(fodder_list)]//100
        if ftype == 'skill': cost *= 2
        acc_cost += cost
        new_exp += gained_exp
        return Card(self.rarity, exp=new_exp, gained_exp=gained_exp, cost=cost, acc_cost=acc_cost)

    def calculate_gained_exp(self, fodder_list, rate=1):
        gained_exp = 0
        for fodder in fodder_list:
            fodder_exp = 0
            level_exp = exp_factor[(self.rarity, fodder.rarity)]
            if fodder.level == 1:
                fodder_exp = level_exp
            else:
                fodder_exp = level_exp*(fodder.level-1) + fodder.exp/100
            gained_exp += int(fodder_exp*rate)
        return gained_exp

    def get_exp_per_coin(self):
        return self.gained_exp/self.acc_cost

    def __mul__(self, num):
        copies = list()
        for i in xrange(num):
            copies.append(deepcopy(self))
        return copies

    def __str__(self):
        ato = Card.get_ato(self.exp)
        ratio = self.get_exp_per_coin()
        # return "== [{}] LEVEL:{} EXP:{} ATO:{} == GAINED EXP:{} COST:{} ACCUMULATIVE COST:{}".format(
        #     self.rarity, self.level, self.exp, ato, self.gained_exp, self.cost, self.acc_cost)
        return dedent("""\
            ==== [%(rty)s] LEVEL:%(lvl)s EXP:%(exp)s ATO:%(ato)s ====
            From fusion: 
                FUSION COST:%(fcost)s ACCUMULATIVE COST:%(acost)s
                GAINED EXP:%(gexp)s

            GAINED EXP / ACCUMULATIVE COST = %(ratio)s""" 
            % {'rty':self.rarity, 'lvl':self.level, 'exp':self.exp, 'ato':ato,
                'gexp':self.gained_exp, 'fcost':self.cost, 'acost':self.acc_cost,
                'ratio':ratio})

    def __repr__(self):
        return "Card({}, exp={}, level={})".format(repr(self.rarity), self.exp, self.level)

    @staticmethod
    def calculate_level(exp):
        index = bisect(exp_to_level.keys(), exp)
        return exp_to_level.values()[index-1]

    @staticmethod
    def get_min_exp(level):
        return exp_to_level.keys()[level-1]

    @staticmethod
    def get_ato(exp):
        index = bisect(exp_to_level.keys(), exp)
        return exp_to_level.keys()[index] - exp

    @staticmethod
    def get_exp_from_ato(level, ato):
        curr_level_exp = exp_to_level.keys()[level-1] 
        next_level_exp = exp_to_level.keys()[level] 
        exact_exp = next_level_exp - ato
        if exact_exp < curr_level_exp:
            raise ValueError("Ato exp does not match current level.")
        return exact_exp

class Interpreter(object):
    """docstring for Interpreter"""
    def __init__(self, arg):
        super(Interpreter, self).__init__()
        self.arg = arg
        

def fusion_permutations(rate=1):
    from itertools import combinations_with_replacement

    base_card = Card('SS', level=30)
    to_sort = list()
    n = ['N', 'R', 'RR', 'S']
    for lf_rarity in n:
        leveled_fodder = Card(lf_rarity)
        for k in xrange(1,10+1):
            subsets = list(combinations_with_replacement(n,k))
            for s in subsets:
                c = Counter(s)
                # print ' '.join(["%s:%d" % (rarity, c[rarity]) for rarity in n])
                mats = ' '.join(["%s:%d" % (rarity, c[rarity]) for rarity in n])
                materials = [Card(rarity) for rarity in s]
                lf = leveled_fodder.fuse_with(materials, rate=rate)
                final = base_card.fuse_with([lf], rate=rate)
                direct_fuse_exp = base_card.calculate_gained_exp(materials + [leveled_fodder], rate)
                exp_efficiency = final.gained_exp/direct_fuse_exp
                # print final, final.get_exp_per_coin()
                to_sort.append((final.get_exp_per_coin(), lf.rarity, lf.level, mats, exp_efficiency))
    done_sort = (sorted(to_sort, reverse=True, key=lambda r: r[0]))
    # print '\n'.join([str(x) for x in done_sort])
    print '\n'.join(["Exp/coin: {:.5f}  Exp%: {:.2%}  recipe: {}({})".format(x[0], x[4], x[1], x[3]) for x in done_sort])

def possible_fuses(base_card, material_counter, ftype="weapon", rate=1):
    from itertools import combinations_with_replacement

    if not isinstance(material_counter, Counter):
        material_counter = Counter(material_counter)

    to_sort = list()
    # n = ['N', 'R', 'RR', 'S']
    n = [r for r in material_counter.keys() if material_counter[r] > 0]
    for lf_rarity in n:
        leveled_fodder = Card(lf_rarity)
        for k in xrange(1,10+1):
            subsets = list(combinations_with_replacement(n,k))
            for s in subsets:
                c = Counter(s)
                remaining = material_counter.copy()
                remaining.subtract(Counter({lf_rarity:1}))
                remaining.subtract(c)
                if any(num < 0 for num in remaining.itervalues()):
                    continue

                mats = ' '.join(["%s:%d" % (rarity, c[rarity]) for rarity in n])
                materials = [Card(rarity) for rarity in s]
                lf = leveled_fodder.fuse_with(materials, ftype=ftype, rate=rate)
                final = base_card.fuse_with([lf], ftype=ftype, rate=rate)
                direct_fuse_exp = base_card.calculate_gained_exp(materials + [leveled_fodder], rate=rate)
                exp_efficiency = final.gained_exp/direct_fuse_exp
                # to_sort.append((final.get_exp_per_coin(), lf.rarity, lf.level, mats, exp_efficiency, final.gained_exp))
                to_sort.append({
                    'exp_per_coin':final.get_exp_per_coin(), 
                    'fodder_rarity':lf.rarity, 
                    'fodder_level':lf.level, 
                    'materials':mats, 
                    'exp_efficiency':exp_efficiency, 
                    'exp_to_base':final.gained_exp,
                    'total_cost':final.acc_cost,
                    'final_level':final.level,
                    'final_ato':final.get_ato(final.exp),
                    'fodder_counts':c + Counter({lf_rarity:1})})
    done_sort = (sorted(to_sort, reverse=True, key=lambda r: r['exp_per_coin']))
    return done_sort


def main():
    parser = argparse.ArgumentParser(description='Get efficient fuses.')
    parser.add_argument('--N', type=int, default=0, help="number of cards")
    parser.add_argument('--R', type=int, default=0, help="number of cards")
    parser.add_argument('--RR', type=int, default=0, help="number of cards")
    parser.add_argument('--S', type=int, default=0, help="number of cards")
    parser.add_argument('--SS', type=int, default=0, help="number of cards")
    parser.add_argument('--rate', type=float, default=1, help="exp rate")
    parser.add_argument('--br', type=str, default="SS", help="base rarity")
    parser.add_argument('--bl', type=int, default=40, help="base level")
    args = parser.parse_args()
    # fodders = Card('R')*6 + Card('RR')*3
    # print fodders
    # stage1 = Card('RR').fuse_with(fodders)
    # print stage1
    # print Card('SS', level=26).fuse_with(stage1*10)

    # fodders = Card('R')*11
    # print fodders
    # stage1 = Card('RR').fuse_with(fodders)
    # print stage1
    # print Card('SS', level=41).calculate_gained_exp(fodders)
    # fusion_permutations()

    # possible_fuses(Card('SS', level=41), {'N':1, 'R':0, 'RR':5})
    # fuses = possible_fuses(Card('SS', level=41), Counter({'N':0, 'R':11, 'RR':11, 'S':0}), ftype="skill", rate=1.5)
    # print '\n'.join(["Exp/coin: {:.5f}  Exp%: {:.2%}  Gained: {}  recipe: {}({})  Cost:{}".format(x['exp_per_coin'], x['exp_efficiency'], x['exp_to_base'], x['fodder_rarity'], x['materials'], x['total_cost']) for x in fuses])
    try:
        fuses = possible_fuses(Card(args.br, level=args.bl), Counter({'N':args.N, 'R':args.R, 'RR':args.RR, 'S':args.S}), ftype="skill", rate=args.rate)
        exp_efficiency_sort = sorted(fuses, reverse=True, key=lambda r: r['exp_efficiency'])
        best = exp_efficiency_sort[0]
        print "{}\n{}".format(best['fodder_rarity'], best['materials'])
    except IndexError:
        print "None"

if __name__ == '__main__':
    main()

