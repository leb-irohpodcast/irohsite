---
layout: default
description: "Multinational morning drive-time radio from Rio, Knoxville and the Twin Cities: automotive excellence, strange tales from beyond and the Global Fleet of Hammpions."
image: /_images/IROH_Banner3.png
---

{% assign episodes = site.data.episodes.episodes %}
{% assign latest = episodes | first %}
{% assign bulletin = site.data.network_bulletin %}
{% assign bulletin_posts = bulletin.posts %}
{% assign active_poll = site.data.current_poll %}
{% assign instagram = site.data.instagram_posts %}

{% include iroh-masthead.html %}

{% if latest %}
<section class="radio-box now-playing-box" id="now-playing" aria-labelledby="now-playing-title">
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

      <h2>
        <a class="broadcast-title-link" href="{{ latest.episode_path | relative_url }}">
          {{ latest.title | escape }}
        </a>
      </h2>

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
      <div class="listen-console">
        <p class="listen-console__label">
          <span>HBI streaming audio</span>
          <strong>Listen now</strong>
        </p>
        <audio controls preload="metadata" src="{{ latest.audio_url | escape }}">
          <a href="{{ latest.audio_url | escape }}">Listen to the episode</a>
        </audio>
      </div>
      {% endif %}

      <p class="broadcast-links">
        <a href="{{ latest.episode_path | relative_url }}">Broadcast page</a>
        <span aria-hidden="true">|</span>
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

<div class="page-columns">
  <main class="main-column">
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

            <h3>
              <a class="broadcast-title-link" href="{{ episode.episode_path | relative_url }}">
                {{ episode.title | escape }}
              </a>
            </h3>

            <p class="broadcast-meta">
              <time datetime="{{ episode.published }}">
                {{ episode.published | date: "%B %-d, %Y" }}
              </time>
              {% if episode.duration != "" %}
                &nbsp;|&nbsp; {{ episode.duration }}
              {% endif %}
            </p>

            {% if episode.audio_url != "" %}
            <div class="listen-console listen-console--compact">
              <p class="listen-console__label">
                <span>HBI audio archive</span>
                <strong>Listen now</strong>
              </p>
              <audio controls preload="none" src="{{ episode.audio_url | escape }}">
                <a href="{{ episode.audio_url | escape }}">Listen to the episode</a>
              </audio>
            </div>
            {% endif %}

            <p class="broadcast-links">
              <a href="{{ episode.episode_path | relative_url }}">Broadcast page</a>
              <span aria-hidden="true">|</span>
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

    {% if instagram.posts and instagram.posts.size > 0 %}
    <section class="radio-box picture-wire" id="picture-wire" aria-labelledby="picture-wire-title">
      <h2 class="radio-box__title" id="picture-wire-title">Behind the Scenes at HBI</h2>

      <p class="picture-wire__intro">
        <strong>New pictures!</strong>
        Dispatches from the Global Fleet and all three HBI bureaus.
        Click a picture for the complete transmission.
      </p>

      <div class="picture-wire__grid">
        {% for post in instagram.posts limit: 6 %}
        <figure class="picture-card">
          <a class="picture-card__image" href="{{ post.url | escape }}">
            <img
              src="{{ post.image | relative_url }}"
              alt="{{ post.alt | default: '' | escape }}"
              loading="lazy"
              decoding="async">
            <span class="picture-card__kind">{{ post.kind_label | default: 'PHOTO' | escape }}</span>
          </a>
          <figcaption>
            <p class="picture-card__dateline">
              <time datetime="{{ post.published | escape }}">{{ post.published | date: "%b %-d, %Y" }}</time>
              {% if post.bureau and post.bureau != "" %}&bull; {{ post.bureau | escape }}{% endif %}
            </p>
            <h3><a href="{{ post.url | escape }}">{{ post.title | escape }}</a></h3>
            {% if post.caption and post.caption != "" %}
            <p class="picture-card__caption">{{ post.caption | escape | truncatewords: 28 }}</p>
            {% endif %}
            {% if post.author and post.author != "" %}
            <p class="picture-card__byline">Filed by {{ post.author | escape }}</p>
            {% endif %}
          </figcaption>
        </figure>
        {% endfor %}
      </div>

      <p class="box-footer-link picture-wire__footer">
        <span>Picture wire last checked {{ instagram.updated_at | date: "%b %-d, %Y" }}</span>
        <a href="{{ instagram.source_url | escape }}">More pictures at {{ instagram.handle | escape }} &raquo;</a>
      </p>
    </section>
    {% endif %}
  </main>

  <aside class="side-column" aria-label="Show information">
    <section class="radio-box" id="about-iroh" aria-labelledby="about-iroh-title">
      <h2 class="radio-box__title" id="about-iroh-title">About IROH</h2>
      <div class="radio-box__content about-iroh">
        <p class="about-iroh__tagline">
          Morning drive-time radio from Rio, Knoxville and the Twin Cities — now on the World Wide Web.
        </p>
        <p>
          Sit back with Caleb, Geno and Justin “The Juice” for automotive excellence,
          tales from the beyond and dispatches from the Global Fleet of Hammpions.
        </p>
      </div>
    </section>

    <section class="radio-box" id="broadcast-schedule">
      <h2 class="radio-box__title">Broadcast schedule</h2>
      <div class="radio-box__content">
        <div class="next-transmission" data-next-transmission>
          <p class="next-transmission__label">Next network transmission</p>
          <p class="next-transmission__countdown" data-next-transmission-countdown role="timer">
            Calculating network time&hellip;
          </p>
          <dl class="next-transmission__times">
            <div>
              <dt>Rio de Janeiro</dt>
              <dd><time data-next-transmission-time="America/Sao_Paulo">Friday, midnight BRT</time></dd>
            </div>
            <div>
              <dt>Knoxville</dt>
              <dd><time data-next-transmission-time="America/New_York">Thursday, 11 PM Eastern</time></dd>
            </div>
            <div>
              <dt>Twin Cities</dt>
              <dd><time data-next-transmission-time="America/Chicago">Thursday, 10 PM Central</time></dd>
            </div>
          </dl>
          <p class="next-transmission__feed">Network feed: Friday 03:00 UTC</p>
        </div>
        <p>Available on HBI and in syndication via select global distribution partners.</p>
      </div>
    </section>

    <section class="radio-box" id="syndication-partners">
      <h2 class="radio-box__title">Distribution Partners</h2>
      <div class="radio-box__content syndication-partners">
        <p class="syndication-group">Global distribution</p>
        <ul class="link-list">
          {% for partner in site.data.syndication_partners.directories %}
          <li><a href="{{ partner.url | escape }}">{{ partner.name | escape }}</a></li>
          {% endfor %}
        </ul>

        <p class="syndication-group">Open-source receivers</p>
        <ul class="link-list">
          {% for partner in site.data.syndication_partners.open_source %}
          <li><a href="{{ partner.url | escape }}">{{ partner.name | escape }}</a></li>
          {% endfor %}
        </ul>

        <p class="syndication-rss">
          <a href="https://pinecast.com/feed/iroh">Broadcast RSS Feed</a>
          for Kasts and other compatible receivers.
        </p>
      </div>
    </section>

    <section class="radio-box" id="network-desk">
      <h2 class="radio-box__title">HBI Network Desk</h2>
      <div class="radio-box__content network-desk">
        <p class="network-status">
          <span class="live-light" aria-hidden="true"></span>
          <strong>Network status: On the air</strong>
        </p>

        <dl class="bureau-clocks" aria-label="Current time at each HBI bureau">
          <div>
            <dt>Rio de Janeiro</dt>
            <dd><time data-bureau-clock="America/Sao_Paulo">--:--</time></dd>
          </div>
          <div>
            <dt>Knoxville</dt>
            <dd><time data-bureau-clock="America/New_York">--:--</time></dd>
          </div>
          <div>
            <dt>Twin Cities</dt>
            <dd><time data-bureau-clock="America/Chicago">--:--</time></dd>
          </div>
        </dl>

        <p class="desk-update">
          Network listings last updated<br>
          <time datetime="{{ site.time | date_to_xmlschema }}">
            {{ site.time | date: "%B %-d, %Y at %H:%M UTC" }}
          </time>
        </p>
      </div>
    </section>

    <section class="radio-box" id="network-bulletin">
      <h2 class="radio-box__title">Network Bulletin</h2>
      <div class="network-bulletin">
        {% if bulletin_posts and bulletin_posts.size > 0 %}
          {% for dispatch in bulletin_posts %}
          <article class="bulletin-dispatch">
            <p class="bulletin-date">
              <time datetime="{{ dispatch.created_at }}" data-bulletin-time>
                {{ dispatch.created_at | date: "%b %-d, %Y · %-I:%M %p UTC" }}
              </time>
            </p>
            <p>{{ dispatch.text | truncatewords: 38 | escape | newline_to_br }}</p>
            <p class="bulletin-link"><a href="{{ dispatch.url | escape }}">Read dispatch &raquo;</a></p>
          </article>
          {% endfor %}
        {% else %}
          <p class="bulletin-empty">The network wire is temporarily quiet.</p>
        {% endif %}

        <p class="bulletin-source">
          <a href="{{ bulletin.source_url | default: 'https://bsky.app/profile/irohpodcast.com' }}">
            More bulletins from IROH on Bluesky
          </a>
        </p>
      </div>
    </section>

    {% comment %}
      The Listener Poll is intentionally absent while polls.json has
      "enabled": false. The scheduled poll structure and the former manual
      question remain ready for use without publishing an unfinished poll.
    {% endcomment %}
    {% if active_poll.enabled %}
    <section class="radio-box" id="listener-poll">
      <h2 class="radio-box__title">Listener Poll</h2>
      <form
        class="listener-poll"
        data-listener-poll
        data-poll-id="{{ active_poll.id | escape }}"
        data-poll-question="{{ active_poll.question | escape }}">
        <fieldset>
          <legend>{{ active_poll.question | escape }}</legend>
          {% for option in active_poll.options %}
          <label>
            <input type="radio" name="poll-option" value="{{ option | escape }}">
            {{ option | escape }}
          </label>
          {% endfor %}
        </fieldset>
        <button type="submit">Transmit ballot</button>
        <p class="poll-explainer">Ballots are delivered through the HBI mailbag. Results are entirely unscientific.</p>
        <p class="poll-status" data-poll-status role="status" hidden></p>
      </form>
    </section>
    {% endif %}

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

    <section class="radio-box" id="from-the-bureaus">
      <h2 class="radio-box__title">From the Bureaus</h2>
      <div class="bureau-list">
        <article class="bureau-report">
          <img src="{{ '/_images/NewIROHLogo-BR.svg' | relative_url }}" alt="IROH Rio de Janeiro studio logo" loading="lazy">
          <h3>Rio de Janeiro</h3>
          <p><strong>Caleb</strong> reports in from the Sixth Brazilian Republic.</p>
        </article>
        <article class="bureau-report">
          <img src="{{ '/_images/NewIROHLogo-TN.svg' | relative_url }}" alt="IROH Knoxville studio logo" loading="lazy">
          <h3>Knoxville</h3>
          <p><strong>Justin “The Juice”</strong> covers the Appalachian motoring desk.</p>
        </article>
        <article class="bureau-report">
          <img src="{{ '/_images/NewIROHLogo-MN.svg' | relative_url }}" alt="IROH Twin Cities studio logo" loading="lazy">
          <h3>Twin Cities</h3>
          <p><strong>Geno</strong> monitors fleet operations and northern dispatches.</p>
        </article>
      </div>
    </section>

    <section class="radio-box">
      <h2 class="radio-box__title">Contact the show</h2>
      <div class="radio-box__content">
        <p>Corrections, automotive heresy and listener dispatches are welcome.</p>
        <ul class="link-list">
          <li><a href="mailto:mailbag@irohpodcast.com">E-mail the mailbag</a></li>
          <li><a href="https://bsky.app/profile/irohpodcast.com">IROH on Bluesky</a></li>
          <li><a href="https://www.instagram.com/iroh_show/">IROH on Instagram</a></li>
          <li><a href="https://pinecast.com/feed/iroh">Broadcast RSS Feed</a></li>
          <li><a href="https://www.youtube.com/@irohshow">Broadcasts on YouTube</a></li>
        </ul>
      </div>
    </section>
  </aside>
</div>
