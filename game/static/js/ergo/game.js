$(document).ready(function() {
    var events_queue = [];

    function ergo_submit() {

    }

    setInterval(function() {
        if (events_queue.length) {
            $.post("/game/", {
                json: JSON.stringify({
                    session_id: session_id,
                    events: events_queue
                })
            });
            events_queue = [];
        }
    }, 2000);
    console.log(session_id);
    $.getJSON("/game/?session_id=" + String(session_id)).done(function(json) {
        var card_template =
            '<div id="card-$card_DOM_id$" class="ergo-card-container">' +
                '<div class="ergo-card" draggable="true" data-card-id="$card_id$" style="background-image: url(\'/static/img/cards/card_$img$.png\'); background-size: contain;"></div>' +
            '</div>';

        var colors = ["#000000", "#8B0000", "#FF8C00", "#006400", "#00008B", "#9400D3"];
        var i, j;

        var lines = json['lines'];
        for (i = 0; i != lines.length; ++i) {
            var $line =  $("#line-" + String(i + 1));
            var line = lines[i];
            for (j = 0; j != line.length; ++j) {
                $line.append(card_template.replace("$card_DOM_id$", String(i) + "-" + String(j))
                                          .replace("$img$", String(line[j] % 7 + 1))
                                          .replace("$card_id$", line[j]));
            }
        }

        var hand = json['hand'];
        var $hand = $("#ergo-hand");
        for (j = 0; j != hand.length; ++j) {
            $hand.append(card_template.replace("$card_DOM_id$", "h-" + String(j))
                                      .replace("$img$", String(hand[j] % 7 + 1))
                                      .replace("$card_id$", hand[j]));
        }

        var dragSelector = null;
        var $t = $('.ergo-card');

        function refresh_cards() {
            var $lines = $(".ergo-card-line");
            $lines.each(function() {
                var $t = $(this).find(".ergo-card-container");

                if ($t.length == 1) {
                    $t.filter(".ergo-card-empty").css("display", "inline-block");
                } else if ($t.length > 1) {
                    $t.filter(".ergo-card-empty").css("display", "none");
                } else {
                    console.log("Err: Line" + $(this).id + "empty");
                }
            });

            setTimeout(function() {
                $(".ergo-card-line-fan").each(function() {
                    var $cards = $(this).find(".ergo-card");

                    $cards.each(function(i) {
                        var $this = $(this);
                        if ($this.attr("draggable") != "false") {
                            $this.css("transform", "rotate(" + String(-30 + 60 * (i) / ($cards.length - 1)) + "deg)");
                        }
                    });
                });
            }, 1);

            setTimeout(function() {
                $(".ergo-card-line").each(function() {
                    var $cards = $(this).find(".ergo-card");
                    $cards.each(function() {
                        $(this).css("transform", "rotate(0deg)");
                    });
                });
            }, 1);
        }

        refresh_cards();

        $t.on('dragstart', function(e) {
            e.originalEvent.dataTransfer.effectAllowed = 'move';
            e.originalEvent.dataTransfer.setData('text/html', '[for-FF]');
            dragSelector = e.target;

            setTimeout(function() {
                $(dragSelector).css("opacity", "0").css("transition", "transform ease 0.5s")
            }, 10);
        });

        $t.on('dragend drop', function() {
            $(dragSelector).css("opacity", "1");

            var e_card_id = $(dragSelector).attr("data-card-id");
            var t = $(dragSelector).parent().parent().get(0);
            var e_line = t.id;

            if (e_line == "ergo-hand") {
                e_line = 0
            } else {
                e_line = e_line[e_line.length - 1];
            }

            var e_pos_left = 0;

            var $cards = $(t).find(".ergo-card-container").not('.ergo-card-empty');
            var card_container_id = $(dragSelector).parent().get(0).id;

            for (var i = 0; i != $cards.length; ++i) {
                if ($cards.get(i).id == card_container_id) {
                    e_pos_left = i;
                    break;
                }
            }

            events_queue.push([2, e_card_id, e_line, e_pos_left].join(" "));
            refresh_cards();
        });


        $t.on('dragenter', function() {
            var cards = [];
            var a = $(dragSelector).parent().get(0).id, b = $(this).parent().get(0).id;
            var line_a = $(dragSelector).parent().parent().get(0).id;
            var line_b = $(this).parent().parent().get(0).id;

            var buf = null, pos = null;

            var $line_b = $("#" + line_b);

            if (line_a != line_b) {
                $line_b.find(".ergo-card-container").each(function() {
                    var $this = $(this);

                    if ($this.get(0).id == b) {
                        cards.push($("#" + a).detach());
                    }

                    cards.push($this.detach());
                });
            } else {
                $line_b.find(".ergo-card-container").each(function() {
                    var $this = $(this);
                    if (($this.get(0).id == a || $this.get(0).id == b) && a != b) {
                        if (pos != null) {
                            cards[pos] = $this.detach();
                            cards.push(buf);
                        } else {
                            pos = cards.length;
                            buf = $this.detach();
                            cards.push(null);
                        }
                    } else {
                        cards.push($this.detach());
                    }
                });
            }

            while (cards.length) {
                $line_b.append(cards.shift());
            }

            refresh_cards();
        });
    });
});

$(function() {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    var csrftoken = getCookie('csrftoken');

    function csrfSafeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
});