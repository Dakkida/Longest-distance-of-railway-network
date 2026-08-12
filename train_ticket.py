"""
このプログラムは、与えられたグラフにおける最長単純経路を求めるためのアルゴリズムを実装しています。
方針としては、深さ優先探索（DFS）+バックトラッキングを用いて、すべての単純経路を探索し、その中で最も長い経路を見つける方法を採用しています。
"""

import sys
from collections import defaultdict

def input_graph(text):
    """
    この関数では、与えられたテキスト入力から無向グラフを構築します。
    """
    best = {}
    #テキスト処理
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split(",")
        if len(parts) != 3:
            # 想定外の行はスキップ
            continue
        try:
            u = int(parts[0].strip())
            v = int(parts[1].strip())
            d = float(parts[2].strip())
        except ValueError:
            continue
        if u == v:
            continue
        # 無向辺として正規化したキーで、距離が長い方を採用する
        # (逆向き入力で同じ辺が二重登録されるのを防ぐ)
        if u < v:
            key = (u, v)
        else:
            key = (v, u)

        if key not in best or d > best[key]:
            best[key] = d

    graph = defaultdict(list)
    nodes = set()
    for (u, v), d in best.items():
        graph[u].append((v, d))
        graph[v].append((u, d))
        nodes.add(u)
        nodes.add(v)
    return graph, nodes

def longest_path(graph, nodes):
    """全頂点を始点として DFS し、最長単純経路(距離最大)を求める。"""
    best_dist = -1.0
    best_path = []

    # 探索が深くなり得るため再帰上限を引き上げる
    sys.setrecursionlimit(max(10000, len(nodes) * 2 + 1000))

    visited = set()
    path = []

    def dfs(node, dist):
        nonlocal best_dist, best_path
        if dist > best_dist:
            best_dist = dist
            best_path = path.copy()
        for nxt, w in graph[node]:
            if nxt not in visited:
                visited.add(nxt)
                path.append(nxt)
                dfs(nxt, dist + w)
                path.pop()
                visited.remove(nxt)

    for start in sorted(nodes):
        visited.add(start)
        path.append(start)
        dfs(start, 0.0)
        path.pop()
        visited.remove(start)

    # 孤立点のみ(辺が無い)場合も、頂点1つ分の経路を返す
    if not best_path and nodes:
        best_path = [min(nodes)]

    return best_path, best_dist

def main():
    text = sys.stdin.read()
    graph, nodes = input_graph(text)

    path, _dist = longest_path(graph, nodes)

    # 駅IDを通る順に CRLF 区切りで出力
    sys.stdout.write("\r\n".join(str(x) for x in path) + "\r\n")


if __name__ == "__main__":
    main()
