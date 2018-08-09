document.addEventListener("DOMContentLoaded",
function () {
    var search = document.getElementById('search_input');

    function key_up_event(event) {
        if (event.keyCode === 13) {
            var value = search.value;
            if (value.length !== 0) {
                window.location.href = "/qa/search?" + 'q=' + encodeURIComponent(value);
            }
        }
    }

    search.onkeyup = key_up_event;
});

function starAnswer(aId) {
    console.log('star');
    window.location.href = "/qa/answer/" + aId + '/star';
}

function unstarAnswer(aId) {
    window.location.href = "/qa/answer/" + aId + '/unstar';
}

function cancelVoteQuestion(qId) {
    window.location.href = "/qa/question/" + qId + '/unvote' ;
}

function cancelVoteAnswer(aId) {
    window.location.href = "/qa/answer/" + aId + '/unvote' ;
}

function voteQuestion(qId, isUp) {
    var like = isUp ? 1 : -1;
    window.location.href = "/qa/question/" + qId + '/vote?' + 'like=' + encodeURIComponent(like);
}

function voteAnswer(aId, isUp) {
    var like = isUp ? 1 : -1;
    window.location.href = "/qa/answer/" + aId + '/vote?' + 'like=' + encodeURIComponent(like);
}