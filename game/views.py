from django.shortcuts import render
from game.forms import *
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from game import ergo_core as ergo
import json


@login_required(login_url="login/")
def test(request):
    context = {
        'user_email': request.user.email,
    }

    return render(request, "test.html", context)


def register(request):
    context = {
        'registered': False,
    }

    if request.method == 'POST':
        user_form = UserForm(data=request.POST)

        if user_form.is_valid():
            # Prepare data for saving
            user = user_form.save()

            # Hash password
            user.set_password(user.password)
            user.save()

            context['registered'] = True
        else:
            print(user_form.errors)

    else:
        user_form = UserForm()

    context['user_form'] = user_form

    return render(request, "auth/register.html", context)


@login_required(login_url="/login/")
def game(request):
    if request.method == 'GET':
        if 'session_id' not in request.GET and 'create' not in request.GET:
            return HttpResponse('{"status": "Error - Bad Request"}',
                                content_type='application/json')

        if 'init' in request.GET:
            if 'session_id' in request.GET:
                return render(request, "game.html",
                              {'session_id': request.GET['session_id']})

        if 'create' in request.GET:
            pattern = '{"session_id": $session_id$}'

            if 'test' in request.GET:  # TODO: remove
                session_id = ergo.start_new_test_session(request.user.id)
            else:
                session_id = ergo.start_new_session(request.user.id)

            return HttpResponse(pattern.replace(
                "$session_id$", str(session_id)),
                content_type='application/json')

        session = ergo.Session(request.GET['session_id'], request.user.id)

        response = dict()
        response['hand'] = session.player.hand
        response['lines'] = session.game.lines
        response['status'] = 'OK'

        return HttpResponse(json.dumps(response),
                            content_type='application/json')

    if request.method == 'POST':
        try:
            data = json.loads(request.POST["json"])
        except TypeError or ValueError or OverflowError or IndexError:
            return HttpResponse('{"status": "Error - JSON incorrect"}',
                                content_type='application/json')

        if 'session_id' in data and type(data['session_id']) is int:
            session_id = data['session_id']
            session = ergo.Session(session_id, request.user.id)

            for i in data['events']:
                args = i.split()
                if int(args[0]) == ergo.ERGO_EVENT_PLACE:
                    session.move_card(*list(map(int, args[1:])))

            return HttpResponse('{"status": "OK"}',
                                content_type='application/json')

        else:
            return HttpResponse('{"status": "Error - Bad Request"}',
                                content_type='application/json')

    # if request.method == 'POST':
    #
    #
    #
    #
    #     if request.user.id not in session['players']:
    #         return HttpResponse("Request incorrect",
    #                             content_type='text/html')
    #     player_idx = session['players'].index(request.user.id)
    #
    #     if 'lines' in data and type(data['lines']) is list:
    #         for line, idx in enumerate(data['lines']):
    #             temp['table_lines'][idx] = line
    #
    #     if 'hand' in data and type(data['hand']) is list:
    #         temp['player_cards'][player_idx] = data['hand']
    #
    #     ergo.rs.set("g-" + data['session_id'], temp)
    #
    #     # if 'events' in data and type(data['events']) is list:
    #     #     for i in data['events']:
    #     #         if type(i) is list:
    #     #             # PUSH_AFTER takes position of the card in player hand
    #     #             # then the number of the line from top [1 - 4]
    #     #             # then position of the card after which card placed [0 - N]
    #     #             # (0 - push front, N - push back).
    #     #             if i[0] == GAME_PUSH_AFTER:
    #     #                 for j in i[1:]:
    #     #                     if type(j) is not int:
    #     #                         return HttpResponse("Request incorrect",
    #     #                                             content_type='text/html')
    #     #                 temp = session['player_cards'][player_idx]
    #     #                 if 0 <= i[1] <= temp and 0 <= i[]:
    #
    #     return HttpResponse('{"status": "OK"}',
    #                         content_type='application/json')




