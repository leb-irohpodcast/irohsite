(function () {
  "use strict";

  function updateBureauClocks() {
    var now = new Date();
    var clocks = document.querySelectorAll("[data-bureau-clock]");

    clocks.forEach(function (clock) {
      var timeZone = clock.getAttribute("data-bureau-clock");
      var formatter = new Intl.DateTimeFormat("en-US", {
        timeZone: timeZone,
        hour: "numeric",
        minute: "2-digit",
        timeZoneName: "short"
      });

      clock.textContent = formatter.format(now);
      clock.setAttribute("datetime", now.toISOString());
    });
  }

  function connectListenerPoll() {
    var poll = document.querySelector("[data-listener-poll]");
    if (!poll) {
      return;
    }

    var status = poll.querySelector("[data-poll-status]");

    poll.addEventListener("submit", function (event) {
      event.preventDefault();

      var selected = poll.querySelector('input[name="poll-option"]:checked');
      if (!selected) {
        status.hidden = false;
        status.textContent = "Please select a bureau before transmitting your ballot.";
        return;
      }

      var pollId = poll.getAttribute("data-poll-id") || "weekly-poll";
      var question = poll.getAttribute("data-poll-question") || "HBI Listener Poll";
      var subject = "HBI Listener Poll: " + pollId;
      var body = [
        question,
        "",
        "My vote: " + selected.value,
        "",
        "Sent from the Listener Poll at IROHpodcast.com."
      ].join("\n");

      status.hidden = false;
      status.textContent = "Opening your e-mail program to deliver the ballot to HBI…";
      window.location.href = "mailto:mailbag@irohpodcast.com?subject=" +
        encodeURIComponent(subject) + "&body=" + encodeURIComponent(body);
    });
  }

  updateBureauClocks();
  window.setInterval(updateBureauClocks, 30000);
  connectListenerPoll();
}());
