---
layout: default
description: "Multinational morning drive-time radio from Rio, Knoxville and the Twin Cities: automotive excellence, tales from beyond and the Global Fleet of Hammpions."
image: /_images/IROH_Banner3.png
---

{% assign episodes = site.data.episodes.episodes %}
{% assign latest = episodes | first %}

{% include iroh-masthead.html %}

<section class="welcome-box">
  <p class="welcome-label">Welcome to IROHpodcast.com</p>
  <h1>Morning drive-time radio from Rio, Knoxville and the Twin Cities — Now on the World Wide Web.</h1>
  <p>
    Sit back with Caleb, Geno and Justin “The Juice” for automotive excellence,
    tales from the beyond and the latest dispatches from the Global Fleet of Hammpions.
  </p>
</section>

<div class="page-columns">
  <main class="main-column">
    {% if latest %}
    <section class="radio-box" id="now-playing" aria-labelledby="now-playing-title">
      <h2 class="radio-box__title" id="now-playing-title">
        <span class="live-light" aria-hidden="true"></span>
        Now on the air
      </h2>

      <article class="featured-broadcast">
        <div class="featured-broadcast__body">
          <p class="broadcast-number">
            {% if latest.episode_number != "" %}
              Broadcast {{ latest.episode_number }}
            {% else %}
              Special transmission
            {% endif %}
          </p>

          <h2>{{ latest.title | escape }}</h2>

          <p class="broadcast-meta">
            <time datetime="{{ latest.published }}">
              {{ latest.published | date: "%B %-d, %Y" }}
            </time>
            {% if latest.duration != "" %}
              &nbsp;|&nbsp; {{ latest.duration }}
            {% endif %}
          </p>

          {% if latest.description_html != "" %}
          {% assign latest_summary = latest.description_text %}
          {% if latest_summary == nil or latest_summary == "" %}
            {% assign latest_summary = latest.description_html | replace: "</h1>", " " | replace: "</h2>", " " | replace: "</h3>", " " | replace: "</p>", " " | replace: "<br>", " " | replace: "<br />", " " | strip_html | remove_first: "Episode Notes" | replace: "Read transcript...", "" | replace: "Read transcript…", "" | strip %}
          {% endif %}
          <p class="broadcast-summary">
            {{ latest_summary | truncatewords: 55 }}
          </p>
          {% endif %}

          {% if latest.audio_url != "" %}
          <audio controls preload="metadata" src="{{ latest.audio_url | escape }}">
            <a href="{{ latest.audio_url | escape }}">Listen to the episode</a>
          </audio>
          {% endif %}

          <p class="broadcast-links">
            {% if latest.transcript_path != "" %}
              <a href="{{ latest.transcript_path | relative_url }}">Read transcript</a>
              <span aria-hidden="true">|</span>
            {% elsif latest.transcript_source_url != "" %}
              <a href="{{ latest.transcript_source_url | escape }}">Read transcript</a>
              <span aria-hidden="true">|</span>
            {% endif %}
            <a href="{{ latest.audio_url | escape }}">Direct MP3</a>
          </p>

          {% if latest.description_html != "" %}
          <details class="broadcast-notes">
            <summary>Broadcast notes</summary>
            <div class="episode-notes">
              {{ latest.description_html }}
            </div>
          </details>
          {% endif %}
        </div>
      </article>
    </section>
    {% endif %}

    <section class="radio-box" aria-labelledby="recent-title">
      <h2 class="radio-box__title" id="recent-title">Recent broadcasts</h2>

      <div class="broadcast-list">
        {% for episode in episodes offset:1 limit:6 %}
        <article class="broadcast-row">
          <div class="broadcast-row__body">
            <p class="broadcast-number">
              {% if episode.episode_number != "" %}
                Broadcast {{ episode.episode_number }}
              {% else %}
                Special transmission
              {% endif %}
            </p>

            <h3>{{ episode.title | escape }}</h3>

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

      <p class="box-footer-link">
        <a href="{{ '/archive/' | relative_url }}">View the complete broadcast archive &raquo;</a>
      </p>
    </section>
  </main>

  <aside class="side-column" aria-label="Show information">
    <section class="radio-box">
      <h2 class="radio-box__title">Broadcast schedule</h2>
      <div class="radio-box__content">
        <p><strong>Thursday, 11 PM Eastern</strong><br>Friday, midnight BRT</p>
        <p>Available on HBI and in syndication via select global distribution partners.</p>
      </div>
    </section>

    <section class="radio-box">
      <h2 class="radio-box__title">Hammpions Broadcast International</h2>
      <div class="radio-box__content station-identification">
        <span class="network-mark-crop">
          <img
            class="network-mark"
            src="{{ '/_images/NewIROHLogo.svg' | relative_url }}"
            alt="International Race of Hammpions logo">
        </span>
        <p>Three studios. Two continents. One epic broadcast.</p>
      </div>
    </section>

    <section class="radio-box">
      <h2 class="radio-box__title">HBI bureaus</h2>
      <div class="bureau-list">
        <figure>
          <img src="{{ '/_images/NewIROHLogo-BR.svg' | relative_url }}" alt="IROH Rio de Janeiro studio logo" loading="lazy">
          <figcaption>Rio de Janeiro</figcaption>
        </figure>
        <figure>
          <img src="{{ '/_images/NewIROHLogo-TN.svg' | relative_url }}" alt="IROH Knoxville studio logo" loading="lazy">
          <figcaption>Knoxville</figcaption>
        </figure>
        <figure>
          <img src="{{ '/_images/NewIROHLogo-MN.svg' | relative_url }}" alt="IROH Twin Cities studio logo" loading="lazy">
          <figcaption>Twin Cities</figcaption>
        </figure>
      </div>
    </section>

    <section class="radio-box">
      <h2 class="radio-box__title">Contact the show</h2>
      <div class="radio-box__content">
        <p>Corrections, automotive heresy and listener dispatches are welcome.</p>
        <ul class="link-list">
          <li><a href="mailto:mailbag@irohpodcast.com">E-mail the mailbag</a></li>
          <li><a href="https://bsky.app/profile/irohpodcast.com">IROH on Bluesky</a></li>
          <li><a href="https://pinecast.com/feed/iroh">Broadcast RSS Feed</a></li>
        </ul>
      </div>
    </section>
  </aside>
</div>

<p class="legal-id">
  The International Race of Hammpions is a production of Hammpions Broadcast International.
</p>
