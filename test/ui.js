function onLoad(event) {
    outfox.init("box", onPageReady);
}

function onPageReady() {
    var buttons = document.getElementsByTagName('button');
    for(var i=0; i < buttons.length; i++) {
        var b = buttons[i];
        b.disabled = false;
    }
}

function test1(button) {
    button.disabled = true;
    var node = document.getElementById('test1-text');
    var token = outfox.addObserver(function(tts, cmd) {
        if(cmd.action == 'finished-say') {
            button.disabled = false;
            tts.removeObserver(token);
        }
    });
    outfox.say(node.innerHTML);
    
}

function test2(button) {
    button.disabled = true;
    var token = outfox.addObserver(function(tts, cmd) {
        if(cmd.action == 'finished-play') {
            button.disabled = false;
            tts.removeObserver(token);
        }
    });
    outfox.play(window.location.href+'/../bell.mp3');
}

function test3(button) {
    var node = document.getElementById('test3-text');
    button.disabled = true;
    var token = outfox.addObserver(function(tts, cmd) {
        if(cmd.action == 'finished-play') {
            button.disabled = false;
            tts.removeObserver(token);
        }
    });
    outfox.say(node.innerHTML);
    outfox.play(window.location.href+'/../bell.wav');
}

function test4(button) {
    var node = document.getElementById('test4-text');
    button.disabled = true;
    var count = 0;
    var callback = function(tts, cmd) {
        if(cmd.action == 'finished-play' || cmd.action == 'finished-say') {
            count++;
        }
        if(count == 2) {
            button.disabled = false;
            tts.removeObserver(token_speech);
            tts.removeObserver(token_sound);
        }
    }
    var token_speech = outfox.addObserver(callback);
    var token_sound =  outfox.addObserver(callback, 1);
    outfox.say(node.innerHTML);
    outfox.play(window.location.href+'/../bell.wav', 1);
}

function test5(button) {
    button.disabled = true;
    var count = 0;
    var token = outfox.addObserver(function(tts, cmd) {
        if(cmd.action == 'finished-say') {
            if(count == 0) {
                count++;
            } else if(count == 1) {
                button.disabled = false;
                tts.removeObserver(token);
            }
        }
    });
    outfox.setProperty('rate', 100);
    outfox.setProperty('volume', 0.3);
    var node = document.getElementById('test5-text1');
    outfox.say(node.innerHTML);
    outfox.setProperty('rate', 500);
    outfox.setProperty('volume', 1.0);
    var node = document.getElementById('test5-text2');
    outfox.say(node.innerHTML);
    outfox.reset();
}

function test6(button) {
    button.disabled = true;
    outfox.setProperty('loop', true);
    outfox.play(window.location.href+'/../bell.wav');
}

function test6Stop() {
    var button = document.getElementById('test6-button');
    button.disabled = false;
    outfox.stop();
    outfox.reset();
}

function test7(button) {
    var logger = document.getElementById('test7-console');
    button.disabled = true;
    var count = 0;
    var callback = function(tts, cmd) {
        logger.innerHTML = JSON.stringify(cmd) + '\n' + logger.innerHTML;
        if(cmd.action == 'finished-play' || cmd.action == 'finished-say') {
            count++;
        }
        if(count == 2) {
            button.disabled = false;
            tts.removeObserver(token_speech);
            tts.removeObserver(token_sound);
        }
    }
    var token_speech = outfox.addObserver(callback, 0);
    var token_sound =  outfox.addObserver(callback, 1);
    var node = document.getElementById('test7-text');
    outfox.say(node.innerHTML, 0, 'my speech name');
    outfox.play(window.location.href+'/../bell.wav', 1, 'my sound name');
}
