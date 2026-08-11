#!/usr/bin/env python3
"""
最長片道きっぷの旅（高速版）
----------------------------
駅(点)と路線(線)からなる鉄道路線網で、同じ駅を2度通らずに
距離の合計がもっとも長くなる片道きっぷの経路を求める。

「最長単純経路問題(Longest Simple Path)」は一般に NP困難だが、
本実装では厳密解(必ず最長)を保ちつつ、総当たりより大幅に速くする
ために次の3つの工夫を入れている。

  1. 連結成分ごとに分割して解く
     最長経路は必ず1つの連結成分の中に収まる。グラフを連結成分に
     分けて別々に解けば、探索空間を成分サイズに縮小できる。

  2. 分枝限定法（枝刈り）
     「残りの駅をあと何個たどれても、使える辺は残り駅数本まで」で
     あることを利用し、その成分で長い辺を上位から足した楽観的上界を
     計算する。現在距離 + 上界 が既知の最長以下なら、その枝は捨てる。
     上界は真の値を必ず上回る(admissible)ので、厳密解は保たれる。

  3. 貪欲な初期解 + 辺を長い順に探索
     まず貪欲法で「そこそこ長い経路」を初期解として確保し、各駅から
     長い辺を優先して探索する。早めに良い解が見つかるほど枝刈りが効く。

入力(標準入力):
    始点ID, 終点ID, 距離        (1行1路線, カンマ区切り, 前後の空白は無視)

出力(標準出力):
    最長経路を構成する駅IDを、通る順に CRLF(\\r\\n) 区切りで出力する。
"""

import sys
from collections import defaultdict


def parse_input(text):
    """入力テキストを無向グラフ(隣接リスト)に変換する。

    - 数値前後の任意個のホワイトスペースを許容。
    - 路線は双方向に通れる無向辺として扱う。
    - 同一駅間に複数路線があれば距離が長い方を採用(単純経路では有利)。
    """
    best = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split(",")
        if len(parts) != 3:
            continue
        try:
            u = int(parts[0].strip())
            v = int(parts[1].strip())
            d = float(parts[2].strip())
        except ValueError:
            continue
        if u == v:
            continue  # 自己ループは寄与しない
        key = (u, v) if u < v else (v, u)
        if key not in best or d > best[key]:
            best[key] = d

    graph = defaultdict(list)
    nodes = set()
    for (u, v), d in best.items():
        graph[u].append((v, d))
        graph[v].append((u, d))
        nodes.add(u)
        nodes.add(v)

    # 探索効率のため、各駅の隣接辺を距離の降順に並べておく
    for u in graph:
        graph[u].sort(key=lambda e: e[1], reverse=True)
    return graph, nodes


def connected_components(graph, nodes):
    """無向グラフを連結成分に分解する。"""
    seen = set()
    comps = []
    for s in nodes:
        if s in seen:
            continue
        stack = [s]
        seen.add(s)
        comp = []
        while stack:
            x = stack.pop()
            comp.append(x)
            for y, _w in graph[x]:
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        comps.append(comp)
    return comps


def greedy_seed(comp_set, graph):
    """各駅から「常に最長の未訪問辺へ進む」貪欲法で初期解を作る。

    厳密ではないが、良い初期下界を素早く得られ、枝刈りが強く効く。
    """
    best_dist = 0.0
    best_path = [next(iter(comp_set))]  # 最低でも駅1つ分
    for start in comp_set:
        visited = {start}
        path = [start]
        dist = 0.0
        node = start
        while True:
            nxt_node = None
            nxt_w = 0.0
            for y, w in graph[node]:  # 降順なので最初に見つかる未訪問が最長
                if y not in visited:
                    nxt_node, nxt_w = y, w
                    break
            if nxt_node is None:
                break
            visited.add(nxt_node)
            path.append(nxt_node)
            dist += nxt_w
            node = nxt_node
        if dist > best_dist:
            best_dist = dist
            best_path = path
    return best_dist, best_path


def solve_component(comp, graph):
    """1つの連結成分の最長単純経路を分枝限定法で厳密に求める。"""
    comp_set = set(comp)
    k = len(comp_set)

    # 単独駅(辺なし)は駅1つ分の経路
    if k == 1:
        return 0.0, [comp[0]]

    # この成分内の無向辺の距離を降順に並べ、上位i本の累積和を用意する。
    # 継続する経路は残り駅数までしか辺を使えないので、
    # 「上位(残り駅数)本の合計」が距離増分の楽観的上界になる。
    edge_w = []
    for u in comp_set:
        for v, w in graph[u]:
            if u < v and v in comp_set:
                edge_w.append(w)
    edge_w.sort(reverse=True)
    prefix = [0.0] * (len(edge_w) + 1)
    for i, w in enumerate(edge_w):
        prefix[i + 1] = prefix[i] + w

    def upper_bound_gain(remaining):
        m = remaining if remaining < len(edge_w) else len(edge_w)
        return prefix[m]

    # 貪欲法で初期解(下界)を確保
    best_dist, best_path = greedy_seed(comp_set, graph)

    visited = set()
    path = []

    def dfs(node, dist):
        nonlocal best_dist, best_path
        if dist > best_dist:
            best_dist = dist
            best_path = path.copy()
        # 枝刈り: 残りの全駅をたどっても best を超えられないなら打ち切る
        remaining = k - len(visited)
        if dist + upper_bound_gain(remaining) <= best_dist:
            return
        for nxt, w in graph[node]:  # 長い辺から試す
            if nxt not in visited:
                visited.add(nxt)
                path.append(nxt)
                dfs(nxt, dist + w)
                path.pop()
                visited.remove(nxt)

    for start in comp:
        visited.add(start)
        path.append(start)
        dfs(start, 0.0)
        path.pop()
        visited.remove(start)

    return best_dist, best_path


def longest_path(graph, nodes):
    """全連結成分を解き、最も長い経路を返す。"""
    sys.setrecursionlimit(max(10000, len(nodes) * 2 + 1000))
    best_dist = -1.0
    best_path = []
    for comp in connected_components(graph, nodes):
        d, p = solve_component(comp, graph)
        if d > best_dist:
            best_dist = d
            best_path = p
    return best_path, best_dist


def main():
    text = sys.stdin.read()
    graph, nodes = parse_input(text)
    if not nodes:
        return
    path, _dist = longest_path(graph, nodes)
    sys.stdout.write("\r\n".join(str(x) for x in path) + "\r\n")


if __name__ == "__main__":
    main()
