# TDE2 — Agente de Ligue 4 (Busca Competitiva)

Inteligência Artificial (PCO118A), PUCPR. Agente de Ligue 4 (7×6, 4 em linha) com
Minimax e poda alfa-beta, avaliado contra um agente aleatório e contra ele mesmo com
profundidade menor.

Só usa a biblioteca padrão do Python 3 (testado no 3.13). Nada para instalar.

## Arquivos

| Arquivo | O que é |
|---|---|
| `game.py` | Regras, estado, ações, resultado, teste-terminal, utilidade (ID2.1) e a avaliação |
| `search.py` | Minimax, alfa-beta, ordenação de jogadas, contador de nós, `best_move` (ID2.2) |
| `verify.py` | Teste de igualdade de valor Minimax × alfa-beta, mais um alfa-beta defeituoso de controle |
| `experiment.py` | Protocolo experimental: partidas, sementes, custo em nós, estatísticas (ID2.3) |
| `saida_verify.txt` | Saída completa da última execução de `verify.py` |
| `resultados.md` | Resultados da última execução de `experiment.py` (100 aberturas, 800 partidas) |
| `partidas.csv` | Uma linha por partida: confronto, abertura, lado, resultado, jogadas, nós |

## Como rodar

```
python3 verify.py                # ~40 s. Deve terminar com "RESULTADO: TUDO OK"
python3 experiment.py            # ~10 min em 2 núcleos. Regrava resultados.md e partidas.csv
python3 experiment.py 10         # versão curta: 10 aberturas por confronto
```

Os dois scripts usam sementes fixas, então rodar de novo dá os mesmos números.

## Convenções

- Todo valor é do ponto de vista de MAX (+1 vitória de MAX, −1 vitória de MIN, 0 empate).
- Unidade de custo: nós visitados (uma chamada da busca = um nó).
- Valor terminal na busca: utilidade × (10 000 − nº de peças jogadas).
- Os agentes de busca usam a mesma avaliação, a mesma ordenação e o mesmo alfa-beta. Só a
  profundidade muda. Nada foi calibrado.
