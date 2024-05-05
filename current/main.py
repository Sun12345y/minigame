import logging

from networkx import Graph

from game import Game
from cops import Cops
from robber import Robber

if __name__ == '__main__':
    logging.basicConfig(filename='run.log', level=logging.INFO)
    main_logger = logging.getLogger('main')
    game = None
    result = 0
    game_status = None

    while result == 0:
        if game is None:
            game = Game(Cops, Robber)
        else:
            game.next_round()
        result = game.result()
        game_status = game.status()
        game_nodes = list(filter(lambda x: isinstance(x[0][0], int), game.graph.nodes.data()))
        main_logger.info('\n{row0}\n{row1}\n{row2}'.format(
            row0=game_nodes[0:3],
            row1=game_nodes[3:6],
            row2=game_nodes[6:9])
        )
    main_logger.info('Result: {result}, status: {status}'.format(result=result, status=game_status))
    if result == -1:  # robber wins
        main_logger.info('Robber wins')
    else:
        main_logger.info('Cops win')
