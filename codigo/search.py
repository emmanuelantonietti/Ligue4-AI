# search.py - a busca do agente: Minimax, alfa-beta e a escolha da melhor jogada.
# Todo valor é do ponto de vista de MAX: valor alto é bom para MAX, valor baixo é bom para MIN.
import math

from game import MAX

INF = math.inf
WIN = 10_000  # valor de uma vitória. A nota de evaluate() fica sempre bem abaixo disso


class Stats:
    """Conta os nós visitados. Cada chamada da busca é um nó. Essa é a unidade de custo."""

    def __init__(self):
        self.nodes = 0


def valor_se_folha(game, s, depth):
    """Se a busca deve parar neste estado, devolve o valor dele. Senão devolve None."""
    if game.terminal(s):
        # Vitória mais cedo vale mais (e derrota mais tarde dói menos),
        # para o agente não adiar uma vitória que já é certa.
        return game.utility(s) * (WIN - game.plies(s))
    if depth <= 0:
        return game.evaluate(s)  # acabou a profundidade: usa a nota da posição
    return None


def acoes(game, s, ordered):
    """As jogadas possíveis, com ou sem a ordenação do centro para as bordas."""
    return game.ordered_actions(s) if ordered else game.actions(s)


def minimax(game, s, depth=INF, stats=None, ordered=False):
    """Valor do estado s, olhando todas as jogadas até a profundidade dada.
    MAX escolhe a jogada de maior valor e MIN a de menor valor."""
    if stats is None:
        stats = Stats()
    stats.nodes += 1
    valor = valor_se_folha(game, s, depth)
    if valor is not None:
        return valor

    valores = [minimax(game, game.result(s, a), depth - 1, stats, ordered)
               for a in acoes(game, s, ordered)]
    return max(valores) if game.player(s) == MAX else min(valores)


def alphabeta(game, s, depth=INF, alpha=-INF, beta=INF, stats=None, ordered=True):
    """Dá o MESMO valor do Minimax, mas visita menos nós porque poda ramos inúteis.
    alpha = melhor valor que MAX já tem garantido. beta = melhor valor (o menor) que MIN já tem."""
    if stats is None:
        stats = Stats()
    stats.nodes += 1
    valor = valor_se_folha(game, s, depth)
    if valor is not None:
        return valor

    if game.player(s) == MAX:
        melhor = -INF
        for a in acoes(game, s, ordered):
            melhor = max(melhor, alphabeta(game, game.result(s, a), depth - 1, alpha, beta, stats, ordered))
            if melhor >= beta:  # MIN já tem uma opção melhor em outro ramo e não deixaria chegar aqui
                return melhor   # PODA: não olha as outras jogadas
            alpha = max(alpha, melhor)
        return melhor

    melhor = INF
    for a in acoes(game, s, ordered):
        melhor = min(melhor, alphabeta(game, game.result(s, a), depth - 1, alpha, beta, stats, ordered))
        if melhor <= alpha:  # MAX já tem uma opção melhor em outro ramo e não deixaria chegar aqui
            return melhor    # PODA
        beta = min(beta, melhor)
    return melhor


def best_move(game, s, depth, ordered=True, stats=None):
    """Escolhe a melhor coluna para quem joga em s. Devolve (coluna, valor).
    Cada jogada é avaliada sem cortes na raiz, para o valor de cada uma ser exato."""
    if stats is None:
        stats = Stats()
    sinal = game.player(s)  # +1 se joga MAX, -1 se joga MIN: assim "maior" é sempre "melhor"
    melhor_jogada, melhor_valor = None, -INF
    for a in acoes(game, s, ordered):
        valor = sinal * alphabeta(game, game.result(s, a), depth - 1, stats=stats, ordered=ordered)
        if valor > melhor_valor:  # em empate fica a primeira, que é a mais central
            melhor_jogada, melhor_valor = a, valor
    return melhor_jogada, sinal * melhor_valor
