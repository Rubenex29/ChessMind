# ChessMind — O que tenho de fazer

O ChessMind é uma aplicação que analisa as tuas partidas de xadrez, identifica erros que repetes e cria exercícios para melhorares essas dificuldades.

Por exemplo: importas dez partidas e a aplicação descobre que, em várias delas, deixaste peças sem proteção. Mostra as posições que sustentam essa conclusão e transforma algumas em exercícios.

Este guia resume a especificação `ChessMind_Project_Specification.pdf`, versão 1.0. Consulta o PDF para os requisitos detalhados.

## 1. Importar partidas

Ler ficheiros **PGN**, que guardam os jogadores, o resultado e a sequência de jogadas de uma partida.

Para cada jogada, guardar a posição anterior e a jogada efetuada. Usa `python-chess` para interpretar as partidas, representar o tabuleiro e verificar jogadas legais. A posição pode ser guardada em **FEN**, um formato de texto que descreve o estado do jogo.

Também deves tratar partidas incompletas e ficheiros inválidos, apresentando erros compreensíveis.

## 2. Analisar as jogadas com Stockfish

O Stockfish é um programa externo que avalia posições e sugere melhores jogadas. A tua aplicação deve iniciá-lo, configurar a análise e terminar o processo corretamente.

Para cada jogada analisada, guardar:

- A jogada feita pelo jogador.
- A melhor jogada encontrada pelo Stockfish.
- As avaliações necessárias para comparar as alternativas.
- Quanto o jogador perdeu em avaliação por escolher aquela jogada.
- Uma classificação, como imprecisão, erro ou erro grave.
- A sequência de continuação sugerida pelo motor.
- A versão do Stockfish e a configuração de análise utilizada.

A perda de avaliação pode ser medida em **centipawns**, em que 100 representam uma unidade de peão. Compara sempre avaliações na mesma perspetiva e com a mesma configuração. As avaliações de mate devem ser tratadas separadamente dos valores normais.

Os limites das classificações são escolhas da aplicação: devem ser configuráveis e documentados.

## 3. Identificar razões concretas para os erros

Criar regras que detetem situações como:

- Deixar uma peça que o adversário pode capturar sem compensação.
- Não aproveitar uma captura vantajosa.
- Mover a dama repetidamente no início.
- Atrasar o desenvolvimento das peças.

Cada deteção deve guardar a evidência: partida, posição, jogada e dados que justificam a conclusão. Uma avaliação pior, por si só, não explica a razão do erro.

Estas regras são os teus **detetores**. Devem indicar a confiança da deteção e admitir que, por vezes, não há evidência suficiente para concluir algo.

## 4. Construir um perfil persistente do jogador

Juntar os resultados de várias partidas para descobrir padrões.

Um erro isolado não chega para dizer que tens uma dificuldade recorrente. A aplicação deve medir quantas vezes acontece, em quantas partidas, a gravidade e se estás a melhorar.

Um exemplo de conclusão seria: «Deixaste peças sem proteção em cinco das últimas doze partidas.» O utilizador deve conseguir consultar as partidas e posições que sustentam essa conclusão.

Os dados devem ficar numa base de dados, para continuarem disponíveis quando fechas e voltas a abrir a aplicação. SQLite é uma opção para começar. Guarda dados estruturados, não apenas frases com conclusões.

## 5. Gerar treino personalizado

Usar posições das tuas próprias partidas como exercícios.

A aplicação mostra uma posição anterior a um erro, pede uma jogada melhor, verifica a resposta e guarda o resultado. Os exercícios devem voltar a aparecer segundo o teu desempenho, usando repetição espaçada.

Cada exercício deve manter a ligação à partida original e ao padrão que pretende treinar. A avaliação da resposta deve basear-se em jogadas legais e na análise do motor.

## 6. Disponibilizar uma API e uma interface básica

No final, o utilizador deve conseguir:

- Importar e analisar partidas.
- Rever jogadas e respetivas evidências.
- Consultar dificuldades recorrentes e a sua evolução.
- Resolver exercícios personalizados.

Uma **API** permite que a interface peça estas operações ao backend. FastAPI é uma opção sugerida na especificação.

Começa pelo terminal para validar a lógica antes de construíres a interface. Mantém a análise independente da apresentação, para poderes usá-la tanto no terminal como na aplicação web.

## 7. Testar, medir e documentar

Verificar que a importação, análise, deteções, perfil e treino funcionam. Inclui casos como roque, promoção, en passant, mate, ficheiros inválidos e falhas do Stockfish.

Também deves medir os erros dos teus próprios detetores: quando identificam corretamente uma situação e quando acusam um problema que não existe. Usa exemplos positivos e negativos, em vez de testar apenas situações em que esperas encontrar um erro.

O README deve explicar:

- O problema que o ChessMind resolve.
- Como instalar e executar com `uv` e Stockfish.
- A arquitetura e o percurso dos dados.
- Como calculas as classificações e os padrões.
- Os resultados reais dos testes e da avaliação dos detetores.
- As limitações conhecidas.
- Como utilizaste assistência de IA durante o desenvolvimento.

## O que é opcional?

- Jogar contra o Stockfish.
- Explicações com um LLM.
- Importação de contas online.
- Suporte para vários utilizadores.
- Funcionalidades avançadas, como pesquisa de erros semelhantes.

O projeto tem de continuar útil sem um LLM. Se adicionares um, ele deve explicar evidências já verificadas; não deve decidir se uma jogada é legal, qual é a melhor jogada ou inventar razões para um erro.

## O que fazer com o código atual?

A especificação pede que uses `python-chess` para o estado do tabuleiro, jogadas legais, PGN, FEN e comunicação com o motor. Implementar todas as regras de xadrez à mão aumenta o trabalho sem avançar o objetivo principal do ChessMind.

Deixa a biblioteca tratar dessas regras e concentra o teu código na análise, nos detetores, no perfil e no treino.

## Ordem recomendada de implementação

1. Confirmar que o projeto instala e executa com `uv` e que o Stockfish está disponível.
2. Aprender a representar e alterar posições com `chess.Board()`.
3. Ler um PGN e imprimir as jogadas no terminal, guardando a posição anterior a cada uma.
4.  Pedir ao Stockfish a avaliação de uma posição.
5. Comparar uma jogada do jogador com a melhor alternativa.
6. Analisar uma partida inteira e produzir resultados estruturados.
7. Criar um primeiro detetor de erros, com exemplos positivos e negativos.
8. Guardar as partidas, análises e evidências numa base de dados.
9. Agregar um tipo de erro entre várias partidas para identificar um padrão.
10. Gerar um exercício a partir de um erro guardado e registar a resposta.
11. Construir a API e a interface sobre essa lógica.
12. Avaliar os resultados, documentar as limitações e preparar uma demonstração.
13. Só depois, acrescentar funcionalidades opcionais.

## Primeira versão pequena e funcional

Para começares, procura completar este fluxo:

**Importar PGN → analisar com Stockfish → guardar erros → identificar um padrão → gerar um exercício.**

Esta primeira versão é um marco de desenvolvimento, não substitui todos os requisitos obrigatórios do PDF. Permite validar o percurso completo antes de aumentares o número de detetores e construíres a interface.

A prioridade agora é conseguir importar uma partida e analisá-la corretamente, porque é essa análise que alimenta o perfil e o treino. Avança em passos pequenos e garante que consegues explicar o código de cada etapa.
