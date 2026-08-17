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

  function localizeBulletinTimes() {
    var bulletinTimes = document.querySelectorAll("[data-bulletin-time]");
    var formatter = new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
      timeZoneName: "short"
    });

    bulletinTimes.forEach(function (bulletinTime) {
      var published = new Date(bulletinTime.getAttribute("datetime"));

      if (Number.isNaN(published.getTime())) {
        return;
      }

      bulletinTime.textContent = formatter.format(published);
      bulletinTime.setAttribute("title", "Displayed in your local timezone");
    });
  }

  function getNextTransmission(now) {
    var transmission = new Date(now.getTime());
    var daysUntilFriday = (5 - now.getUTCDay() + 7) % 7;

    transmission.setUTCDate(now.getUTCDate() + daysUntilFriday);
    transmission.setUTCHours(3, 0, 0, 0);

    if (transmission.getTime() <= now.getTime()) {
      transmission.setUTCDate(transmission.getUTCDate() + 7);
    }

    return transmission;
  }

  function padClockNumber(value) {
    return value < 10 ? "0" + value : String(value);
  }

  function formatCountdown(milliseconds) {
    var totalSeconds = Math.max(0, Math.floor(milliseconds / 1000));
    var days = Math.floor(totalSeconds / 86400);
    var hours = Math.floor((totalSeconds % 86400) / 3600);
    var minutes = Math.floor((totalSeconds % 3600) / 60);
    var seconds = totalSeconds % 60;

    return "T-" + days + "D " + padClockNumber(hours) + ":" +
      padClockNumber(minutes) + ":" + padClockNumber(seconds);
  }

  function formatTransmissionTime(transmission, timeZone) {
    var formatter = new Intl.DateTimeFormat("en-US", {
      timeZone: timeZone,
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      timeZoneName: "short"
    });

    return formatter.format(transmission);
  }

  function updateNextTransmission() {
    var panel = document.querySelector("[data-next-transmission]");

    if (!panel) {
      return;
    }

    var now = new Date();
    var transmission = getNextTransmission(now);
    var countdown = panel.querySelector("[data-next-transmission-countdown]");
    var stationTimes = panel.querySelectorAll("[data-next-transmission-time]");

    if (countdown) {
      var countdownText = formatCountdown(transmission.getTime() - now.getTime());

      countdown.textContent = countdownText;
      countdown.setAttribute("aria-label", "Time until next network transmission: " + countdownText);
      countdown.setAttribute("title", "Next transmission: " + transmission.toISOString());
    }

    stationTimes.forEach(function (stationTime) {
      var timeZone = stationTime.getAttribute("data-next-transmission-time");

      stationTime.textContent = formatTransmissionTime(transmission, timeZone);
      stationTime.setAttribute("datetime", transmission.toISOString());
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
  updateNextTransmission();
  window.setInterval(updateNextTransmission, 1000);
  localizeBulletinTimes();
  connectListenerPoll();
}());
