from aiohttp import web
import random
import string
import chess

players_queue = []
games = {}


number_to_letter_map = {
    0: 'a',
    1: 'b',
    2: 'c',
    3: 'd',
    4: 'e',
    5: 'f',
    6: 'g',
    7: 'h',
}


async def generate_id(request):
    player_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + '-' + \
                ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + '-' + \
                ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + '-' + \
                ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return web.Response(text=player_id)


async def find_player(request):
    player_id = request.match_info.get('id')
    players_queue.append(player_id)
    if len(players_queue) >= 2:
        game = {
            'white': players_queue.pop(),
            'black': players_queue.pop(),
            'turn': 'white',
            'board': chess.Board(),
        }
        games[game['white']] = games[game['black']] = game

    return web.Response(text="Added to queue")


async def leave(request):
    player_id = request.match_info.get('id')
    if player_id in games:
        white = games[player_id]['white']
        black = games[player_id]['black']
        del games[white]
        del games[black]

    return web.Response(text='true')


async def game_exists(request):
    player_id = request.match_info.get('id')
    if player_id in games:
        return web.Response(text='true')
    return web.Response(text='false')


def _get_color(player_id):
    if player_id not in games:
        return None
    if player_id == games[player_id]['white']:
        return 'white'
    else:
        return 'black'


def _get_board(player_id):
    if games[player_id]['white'] == player_id:
        return str(games[player_id]['board']).replace(' ', '').replace("\n", '')
    else:
        return str(games[player_id]['board'])[::-1].replace(' ', '').replace("\n", '')


async def get_board(request):
    player_id = request.match_info.get('id')
    if player_id in games:
        return web.Response(text=_get_board(player_id))
    return web.Response(text='false')


def positionsToText(x1, y1, x2, y2, player_id):
    if _get_color(player_id) == 'white':
        return str(number_to_letter_map[int(x1)]) + str(8 - int(y1)) + \
               str(number_to_letter_map[int(x2)]) + str(8 - int(y2))
    return str(number_to_letter_map[7 - int(x1)]) + str(int(y1) + 1) + \
               str(number_to_letter_map[7 - int(x2)]) + str(int(y2) + 1)


async def move(request):
    player_id = request.match_info.get('id')
    x1 = request.match_info.get('x1')
    y1 = request.match_info.get('y1')
    x2 = request.match_info.get('x2')
    y2 = request.match_info.get('y2')
    move_position = positionsToText(x1, y1, x2, y2, player_id)
    if player_id in games and _get_color(player_id) == games[player_id]['turn']:
        board = games[player_id]['board']
        if chess.Move.from_uci(move_position) in board.legal_moves:
            board.push(chess.Move.from_uci(move_position))
            if games[player_id]['turn'] == 'white':
                games[player_id]['turn'] = 'black'
            else:
                games[player_id]['turn'] = 'white'
            return web.Response(text='true')
    return web.Response(text='false')


async def my_turn(request):
    player_id = request.match_info.get('id')
    if player_id in games and _get_color(player_id) == games[player_id]['turn']:
        return web.Response(text='true')

    return web.Response(text='false')


async def result(request):
    player_id = request.match_info.get('id')
    if player_id in games:
        board: chess.Board = games[player_id]['board']
        if board.outcome() is not None:
            if board.is_variant_draw():
                return web.Response(text='Draw!')
            if board.outcome().winner:
                return web.Response(text='White_won!')
            else:
                return web.Response(text='Black_won!')
    return web.Response(text='false')


app = web.Application()
app.add_routes([
    web.get('/id', generate_id),
    web.get('/find/{id}', find_player),
    web.get('/leave/{id}', leave),
    web.get('/exists/{id}', game_exists),
    web.get('/board/{id}', get_board),
    web.get('/move/{id}/{x1}/{y1}/{x2}/{y2}', move),
    web.get('/turn/{id}', my_turn),
    web.get('/result/{id}', result),
])

if __name__ == '__main__':
    web.run_app(app)
