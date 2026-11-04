# game.py - as regras do Ligue 4: tabuleiro, jogadas, fim de jogo e nota das posições.
from collections import namedtuple

MAX = +1  # jogador que quer o maior valor (suas peças valem +1)
MIN = -1  # jogador que quer o menor valor (suas peças valem -1)

# Um ESTADO do jogo guarda 3 coisas:
#   cols   : as 7 colunas. Cada coluna é uma tupla com as peças de baixo para cima (+1 ou -1)
#   player : de quem é a vez (MAX ou MIN)
#   last   : (coluna, linha) da última peça jogada. Só serve para testar a vitória mais rápido
State = namedtuple("State", ["cols", "player", "last"])

# As 4 direções em que dá para alinhar peças: horizontal, vertical e as duas diagonais
DIRECOES = ((1, 0), (0, 1), (1, 1), (1, -1))


class ConnectK:
    """Ligue 4 com tamanho configurável. Padrão: 7 colunas, 6 linhas, 4 em linha."""

    def __init__(self, ncols=7, nrows=6, k=4):
        self.ncols, self.nrows, self.k = ncols, nrows, k
        # colunas do centro para as bordas: 3, 2, 4, 1, 5, 0, 6 (usada para ordenar as jogadas)
        meio = (ncols - 1) / 2
        self.ordem_das_colunas = sorted(range(ncols), key=lambda c: (abs(c - meio), c))
        # todos os grupos de k casas seguidas do tabuleiro (usados na nota das posições)
        self.janelas = self._todas_as_janelas()

    def _todas_as_janelas(self):
        janelas = []
        for c in range(self.ncols):
            for r in range(self.nrows):
                for dc, dr in DIRECOES:
                    c_fim, r_fim = c + (self.k - 1) * dc, r + (self.k - 1) * dr
                    if 0 <= c_fim < self.ncols and 0 <= r_fim < self.nrows:  # cabe no tabuleiro?
                        janelas.append([(c + i * dc, r + i * dr) for i in range(self.k)])
        return janelas

    # ------------------------------------------------------------------
    # Os componentes da formalização do jogo
    # ------------------------------------------------------------------
    def initial(self):
        """Estado inicial: tabuleiro vazio, vez de MAX."""
        return State(cols=tuple(() for _ in range(self.ncols)), player=MAX, last=None)

    def player(self, s):
        """De quem é a vez."""
        return s.player

    def actions(self, s):
        """Jogadas possíveis: as colunas que ainda não estão cheias."""
        return [c for c in range(self.ncols) if len(s.cols[c]) < self.nrows]

    def result(self, s, a):
        """Novo estado depois de jogar na coluna a. O estado s original não é alterado."""
        coluna = s.cols[a]
        assert len(coluna) < self.nrows, "coluna cheia"
        novas_colunas = list(s.cols)
        novas_colunas[a] = coluna + (s.player,)  # a peça cai no topo da coluna
        return State(tuple(novas_colunas), -s.player, (a, len(coluna)))  # a vez passa ao outro

    def terminal(self, s):
        """O jogo acabou? Sim se alguém alinhou 4 ou se o tabuleiro está cheio (empate)."""
        return self.winner(s) != 0 or self.is_full(s)

    def utility(self, s):
        """Valor de um estado final, sempre do ponto de vista de MAX: +1, -1 ou 0 (empate)."""
        return self.winner(s)

    # ------------------------------------------------------------------
    # Fim de jogo
    # ------------------------------------------------------------------
    def winner(self, s):
        """Quem alinhou 4 peças (+1 = MAX, -1 = MIN) ou 0 se ninguém.
        Só a última peça jogada pode ter completado o alinhamento, então só olhamos ao redor dela."""
        if s.last is None:
            return 0
        c, r = s.last
        cor = s.cols[c][r]
        for dc, dr in DIRECOES:
            # a própria peça + as iguais seguidas num sentido + as iguais seguidas no sentido oposto
            total = 1 + self._contar(s, c, r, dc, dr, cor) + self._contar(s, c, r, -dc, -dr, cor)
            if total >= self.k:
                return cor
        return 0

    def _contar(self, s, c, r, dc, dr, cor):
        """Quantas peças da cor dada há em sequência, a partir de (c, r), andando na direção (dc, dr)."""
        n = 0
        c, r = c + dc, r + dr
        while self.peca(s, c, r) == cor:
            n += 1
            c, r = c + dc, r + dr
        return n

    def peca(self, s, c, r):
        """A peça na casa (coluna c, linha r): +1, -1, ou 0 se está vazia ou fora do tabuleiro."""
        if 0 <= c < self.ncols and 0 <= r < len(s.cols[c]):
            return s.cols[c][r]
        return 0

    def is_full(self, s):
        return all(len(coluna) == self.nrows for coluna in s.cols)

    def plies(self, s):
        """Quantas peças já foram jogadas."""
        return sum(len(coluna) for coluna in s.cols)

    # ------------------------------------------------------------------
    # Ajudas para a busca
    # ------------------------------------------------------------------
    def ordered_actions(self, s):
        """As jogadas possíveis em ordem: colunas do centro primeiro (costumam ser as melhores)."""
        return [c for c in self.ordem_das_colunas if len(s.cols[c]) < self.nrows]

    def evaluate(self, s):
        """Nota de uma posição que ainda não acabou, do ponto de vista de MAX
        (positiva é boa para MAX, negativa é boa para MIN).

        Olha cada janela de 4 casas. Se ela só tem peças de um jogador, ainda pode virar um
        alinhamento dele: vale 1, 10 ou 100 pontos para 1, 2 ou 3 peças. Janela com peças dos
        dois lados vale 0. Cada peça na coluna do meio vale mais 3 pontos."""
        nota = 0
        for janela in self.janelas:
            do_max = do_min = 0  # quantas peças de cada jogador há nesta janela
            for c, r in janela:
                coluna = s.cols[c]
                if r < len(coluna):  # a casa tem peça?
                    if coluna[r] == MAX:
                        do_max += 1
                    else:
                        do_min += 1
            if do_max and not do_min:
                nota += 10 ** (do_max - 1)
            elif do_min and not do_max:
                nota -= 10 ** (do_min - 1)
        nota += 3 * sum(s.cols[self.ncols // 2])  # bônus da coluna do meio
        return nota

    def render(self, s):
        """Desenha o tabuleiro em texto (X = MAX, O = MIN)."""
        simbolo = {MAX: "X", MIN: "O", 0: "."}
        linhas = []
        for r in range(self.nrows - 1, -1, -1):  # de cima para baixo
            linhas.append(" ".join(simbolo[self.peca(s, c, r)] for c in range(self.ncols)))
        linhas.append(" ".join(str(c) for c in range(self.ncols)))
        return "\n".join(linhas)
