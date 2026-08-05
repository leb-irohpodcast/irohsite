---
layout: default
title: Broadcast Archive
description: Every International Race of Hammpions broadcast, newest first, with episode notes, audio and transcripts where available.
image: /_images/IROH_Banner3.png
permalink: /archive/
---

{% assign episodes = site.data.episodes.episodes %}

{% include iroh-masthead.html %}

<section class="radio-box archive-box">
  <h1 class="radio-box__title">HBI broadcast archive</h1>
  <div class="archive-intro">
    <p>Every International Race of Hammpions transmission, newest first.</p>
    <p><a href="{{ '/' | relative_url }}">&laquo; Return to the current broadcast</a></p>
  </div>

  <div class="broadcast-list">
    {% for episode in episodes %}
    <article class="broadcast-row archive-row">
      <div class="broadcast-row__body">
        <p class="broadcast-number">
          {% if episode.episode_number != "" %}
            Broadcast {{ episode.episode_number }}
          {% else %}
            Special transmission
          {% endif %}
        </p>

        <h2>{{ episode.title | escape }}</h2>

        <p class="broadcast-meta">
          <time datetime="{{ episode.published }}">
            {{ episode.published | date: "%B %-d, %Y" }}
          </time>
          {% if episode.duration != "" %}
            &nbsp;|&nbsp; {{ episode.duration }}
          {% endif %}
        </p>

        {% if episode.audio_url != "" %}
        <audio controls preload="metadata" src="{{ episode.audio_url | escape }}">
          <a href="{{ episode.audio_url | escape }}">Listen to the episode</a>
        </audio>
        {% endif %}

        <p class="broadcast-links">
          {% if episode.transcript_path != "" %}
            <a href="{{ episode.transcript_path | relative_url }}">Read transcript</a>
            <span aria-hidden="true">|</span>
          {% elsif episode.transcript_source_url != "" %}
            <a href="{{ episode.transcript_source_url | escape }}">Read transcript</a>
            <span aria-hidden="true">|</span>
          {% endif %}
          <a href="{{ episode.audio_url | escape }}">Direct MP3</a>
        </p>

        {% if episode.description_html != "" %}
        <details class="broadcast-notes">
          <summary>Broadcast notes</summary>
          <div class="episode-notes">
            {{ episode.description_html }}
          </div>
        </details>
        {% endif %}
      </div>
    </article>
    {% endfor %}
  </div>
</section>
