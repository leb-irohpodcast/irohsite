---
layout: default
---

# The International Race of Hammpions Show

Hi, welcome to the International Race of Hammpions. Here’s our [RSS feed](https://pinecast.com/feed/iroh).

We’re also on [Bluesky](https://bsky.app/profile/irohpodcast.com) for updates and other chattering.

Our mailbag is now open at mailbag [at] irohpodcast [dot] com.

## Latest broadcasts

{% for episode in site.data.episodes.episodes %}
<article style="margin-bottom: 2.5rem;">
  <h2>
    <a href="{{ episode.link | default: episode.audio_url }}">
      {{ episode.title | escape }}
    </a>
  </h2>

  <p>
    <small>
      {{ episode.published | date: "%B %-d, %Y" }}
      {% if episode.duration != "" %}
        · {{ episode.duration }}
      {% endif %}
    </small>
  </p>

  {% if episode.audio_url != "" %}
  <audio
    controls
    preload="none"
    src="{{ episode.audio_url }}"
    style="width: 100%;">
  </audio>
  {% endif %}

  {% if episode.description_html != "" %}
  <details style="margin-top: 0.75rem;">
    <summary>Broadcast notes</summary>
    <div style="margin-top: 0.75rem;">
      {{ episode.description_html }}
    </div>
  </details>
  {% endif %}
</article>
{% endfor %}

## Continuous player

<iframe
  src="https://pinecast.com/embed/player_playlist/iroh?color.primary=%23ffffff&amp;color.secondary=%23cbd3da&amp;color.accent=%230066ff"
  style="width:100%;border:0"
  height="270">
</iframe>
