import logging
import traceback

from networkx import Graph

game_logger = logging.getLogger('game')

class Game:
    def __init__(self,
                 cops_engine,
                 robber_engine) -> None:
        """Constructor for the Game class

        The Cops class is available via cops_engine.Cops
        and the Robber class is available via robber_engine.Robber.

        :param cops_engine: engine used for the cops
        :param robber_engine: engine used for the robber
        """
        self.__init_tictactoe_graph()
        self.__result = 0
        self.__round = -1
        self.__status = 'Game continues'

        self.cops = None
        try:
            self.__init_cops(cops_engine)
        except RuntimeError:
            return

        self.robber = None
        try:
            self.__init_robber(robber_engine)
        except RuntimeError:
            return

    def __init_tictactoe_graph(self) -> None:
        """Initialises self.graph.

        The tictactoe graph is a networkx.Graph.
        Nodes are either representing spaces (i,j), rows ('row',i), columns ('col',j), or diagonals ('dia',i).
        Spaces are connected to rows, columns, or diagonals by an edge with respect to their position on the 3x3 tic-tac-toe grid.
        Nodes also contain a label as an attribute, initialized with a space ' '.
        """
        self.graph = Graph()

        for i in range(2):
            self.graph.add_node(('dia', i), label=' ')

        for i in range(3):
            self.graph.add_node(('row', i), label=' ')
            for j in range (3):
                if i == 0:
                    self.graph.add_node(('col', j), label=' ')
                self.graph.add_node((i, j), label=' ')

                self.graph.add_edge((i, j), ('row', i))
                self.graph.add_edge((i, j), ('col', j))
                if i == j:
                    self.graph.add_edge((i, j), ('dia', 0))
                if i == 2-j:
                    self.graph.add_edge((i, j), ('dia', 1))

    def __init_cops(self, cops_engine) -> None:
        """Initialises self.cops.

        If an exception is raised during the initialisation, the exception is logged,
        robber wins and a RuntimeError is raised.

        :param cops_engine: the engine to use to initialise Cops
        """
        try:
            self.cops = cops_engine()
        except Exception as e:
            game_logger.info(traceback.format_exception(type(e), e, e.__traceback__))
            self.__cops_exception()
            raise RuntimeError

    def __init_robber(self, robber_engine) -> None:
        """Initialises self.robber.

        If an exception is raised during the initialisation, the exception is logged,
        cops win and a RuntimeError is raised.

        :param robber_engine: the engine to use to initialise Robber
        """
        try:
            self.robber = robber_engine()
        except Exception as e:
            game_logger.info(traceback.format_exception(type(e), e, e.__traceback__))
            self.__robber_exception()
            raise RuntimeError

    def next_round(self) -> None:
        """Computes a single round of the game.

        Cops have the first move, and then move alternating with the Robber.
        """
        self.__round += 1
        if self.__round % 2 == 0:
            self.__cops_step()
        else:
            self.__robber_step()

    def __robber_step(self) -> None:
        """Computes a single robber step.

        In case of an exception, the exception is logged and the cops win.
        Otherwise, we add the new label given by robber's step method to the graph.
        """
        robber_move: tuple[int, int] | None = None
        try:
            robber_move = self.robber.step(self.graph)
        except Exception as e:
            game_logger.info(traceback.format_exception(type(e), e, e.__traceback__))
            self.__robber_exception()
        self.__set_robber_position(robber_move)
        if self.__three_in_a_row('R'):
            self.__robber_three_in_a_row()

    def __cops_step(self) -> None:
        """Computes a single cops step.

        In case of an exception, the exception is logged and the robber wins.
        Otherwise, we add the new label given by cops' step method to the graph.
        """
        cop_move: tuple[int, int] | None = None
        try:
            cop_move = self.cops.step(self.graph)
        except Exception as e:
            game_logger.info(traceback.format_exception(type(e), e, e.__traceback__))
            self.__cops_exception()
        self.__set_cop_positions(cop_move)
        if self.__three_in_a_row('C'):
            self.__cops_three_in_a_row()
        if self.__game_tied():
            self.__tie()

    def result(self) -> int:
        """Returns the current result of the game.

        :return: 0 if the game continues, -1 if the robber wins, and 1 if the cops win
        """
        return self.__result

    def status(self) -> str:
        """Returns the current status of the game.

        Possible values are
        - Game continues
        - Cops invalid step
        - Robber invalid step
        - Exception in cops call
        - Exception in robber call
        - Robber caught
        """
        return self.__status

    def __set_cop_positions(self, move: tuple[int, int]) -> None:
        """Updates the graph with a 'C' label on node {move} if the given tuple is a valid move

        If the given tuple is None, the robber wins, i.e. __result is set to -1.
        If the given tuple is not a valid move, the robber wins.
        If the given tuple is already labelled, the robber wins.
        Otherwise, adds the next label in the free node.
        :param move: the node to be labelled with 'C' next
        """
        if move is None:
            self.__cops_invalid_step()
            return
        if move[0] < 0 or move[1] < 0 or move[0] > 2 or move[1] > 2 or self.graph.nodes[move]['label'] != ' ':
            self.__cops_invalid_step()
            return
        self.graph.nodes[move]['label'] = 'C'

    def __set_robber_position(self, move: tuple[int, int]) -> None:
        """Updates the graph with an 'R' label on node {move} if the given tuple is a valid move

        If the given position is None, the cop wins, i.e. __result is set to 1.
        If the given position is not a valid position, the cops win.
        If the given position is already labelled, the cops win.
        Otherwise, adds the next label in the free node.
        :param move: the node to be labelled with 'R' next
        """
        if move is None:
            self.__robber_invalid_step()
            return
        if move[0] < 0 or move[1] < 0 or move[0] > 2 or move[1] > 2 or self.graph.nodes[move]['label'] != ' ':
            self.__robber_invalid_step()
            return
        self.graph.nodes[move]['label'] = 'R'

    def __three_in_a_row(self, label: str) -> int:
        """Checks if the game has a winning three labels in-a-row, i.e. a node such that all neighbors share the same label.

        :param label: the label cops and robbers use to play in the graph
        :return: 1 if there are currently three labels in-a-row, and 0 if there are not
        """
        for v in self.graph.nodes:
            win = True
            for w in self.graph.adj[v]:
                if self.graph.nodes[w]['label'] != label:
                    win = False
            if win:
                return 1
        return 0

    def __game_tied(self) -> int:
        """Checks if the game is tied.

        :return: 1 if all (i,j) nodes have labels other than ' ', and 0 if at least one (i,j) node is still labelled with ' '.
        """
        for i in range(3):
            for j in range(3):
                if self.graph.nodes[(i,j)]['label'] == ' ':
                    return 0
        return 1

    def __cops_three_in_a_row(self) -> None:
        """If the cops have three-in-a-row, the cops win and the status of the game is set to 'Robber caught'."""
        self.__cops_win()
        self.__set_status('Robber caught')

    def __tie(self) -> None:
        """If the game ends in a tie, the robber wins and the status of the game is set to 'Cops shift ends'."""
        self.__robber_win()
        self.__set_status('Cops shift ends')

    def __robber_three_in_a_row(self) -> None:
        """If the robber has three-in-a-row, the robber wins and the status of the game is set to 'Robber escapes'."""
        self.__robber_win()
        self.__set_status('Robber escapes')

    def __cops_invalid_step(self) -> None:
        """If the cops make an invalid step, robber wins and the status of the game is set to 'Cops invalid step.'"""
        self.__robber_win()
        self.__set_status('Cops invalid step')

    def __robber_invalid_step(self) -> None:
        """If robber makes an invalid step, the cops win and the status of the game is set to 'Robber invalid step.'"""
        self.__cops_win()
        self.__set_status('Robber invalid step')

    def __cops_exception(self) -> None:
        """If an exception is raised in one of the cop calls, robber wins and the status of the game is set to
        'Exception in cops call'.
        """
        self.__robber_win()
        self.__set_status('Exception in cops call')

    def __robber_exception(self) -> None:
        """If an exception is raised in one of the robber calls, the cops win and the status of the game is set to
        'Exception in robber call'.
        """
        self.__cops_win()
        self.__set_status('Exception in robber call')

    def __robber_win(self) -> None:
        """Sets __result to -1 if the game still continues."""
        if self.__result == 0:
            self.__result = -1

    def __cops_win(self) -> None:
        """Sets __result to 1 if the game still continues."""
        if self.__result == 0:
            self.__result = 1

    def __set_status(self, status: str) -> None:
        """Sets __status to the given value if the game still continues."""
        if self.__status == 'Game continues':
            self.__status = status
