/**
 * Table Generation and Display
 */

function generateTableHTML(songs, currentMetric) {
  // Determine if we're in Spotify view
  const isSpotifyView = window.currentView === 'spotify-trending';
  
  console.log('🔨 Generating table for', songs.length, 'songs, isSpotifyView:', isSpotifyView);
  
  try {
    const rows = songs.map((song, index) => {
      try {
        return generateSongRow(song, index, currentMetric);
      } catch (error) {
        console.error(`❌ Error generating row ${index}:`, error, song);
        return `<tr><td colspan="6">Error loading song ${index + 1}</td></tr>`;
      }
    }).join('');
    
    console.log('✅ Generated', rows.length, 'characters of HTML');
    
    return `
      <table class="results-table">
        <thead>
          <tr>
            <th style="width: 60px; text-align: center;">Rank</th>
            <th style="width: 300px;">Song Title</th>
            <th style="width: 200px;">Record Label</th>
            <th style="width: 100px; text-align: center;">
              <div style="color: #999; font-size: 11px; font-weight: 400;">Metric</div>
              <div style="color: #999; font-size: 11px; font-weight: 400;">descr.</div>
            </th>
            <th style="width: 140px; text-align: right;">
              <div style="display: flex; align-items: center; justify-content: flex-end; gap: 4px;">
                ${isSpotifyView ? `
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="#1DB954">
                    <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
                  </svg>
                  <span>Streams ↓</span>
                ` : `
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                    <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
                  </svg>
                  <span>Creates ↓</span>
                `}
              </div>
            </th>
            <th style="width: 140px; text-align: right;">
              <div style="display: flex; align-items: center; justify-content: flex-end; gap: 4px;">
                ${isSpotifyView ? `
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                    <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.10z"/>
                  </svg>
                  <span>TikTok</span>
                ` : `
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="#1DB954">
                    <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
                  </svg>
                  <span>Streams</span>
                `}
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          ${rows}
        </tbody>
      </table>
    `;
  } catch (error) {
    console.error('❌ Error in generateTableHTML:', error);
    throw error;
  }
}

// Make functions globally available
window.generateTableHTML = generateTableHTML;

function generateSongRow(song, index, currentMetric) {
  // Handle both database format and TikTok trending API format
  const title = song.title || song.song_name || 'Unknown Title';
  const artist = song.artist || song.artist_name || 'Unknown Artist';
  
  // Detect current view
  const isSpotifyView = window.currentView === 'spotify-trending';

  // --- Always compute TikTok data from tiktok_metrics ---
  const tiktokMetrics = song.tiktok_metrics || {};
  let tiktokMainValue;

  if (isSpotifyView) {
    // In Spotify view, show 24h creates for TikTok column
    tiktokMainValue = tiktokMetrics.last_24h_videos || 0;
  } else if (currentMetric.isPercentage) {
    tiktokMainValue = tiktokMetrics.last_24h_percentage || 0;
  } else {
    tiktokMainValue = tiktokMetrics[currentMetric.key] || 0;
  }
  const tiktokPercentage = tiktokMetrics.last_24h_percentage || 0;
  const tiktokTotalValue = tiktokMetrics.total_videos || 0;

  // --- Always compute Spotify data from history.spotify ---
  let spotifyMainValue = 0;
  let spotifySubValue = 0;

  if (song.history && song.history.spotify) {
    const streams = song.history.spotify.streams || [];
    const totalStreams = song.history.spotify.total_streams || 0;

    if (isSpotifyView) {
      // In Spotify view, use Spotify metric keys
      if (currentMetric.key === 'daily_streams') {
        spotifyMainValue = streams.length > 0 ? (streams[streams.length - 1].value || 0) : 0;
        spotifySubValue = totalStreams;
      } else if (currentMetric.key === 'weekly_streams') {
        const last7 = streams.slice(-7);
        spotifyMainValue = last7.reduce((sum, d) => sum + (d.value || 0), 0);
        spotifySubValue = totalStreams;
      } else if (currentMetric.key === 'total_streams') {
        spotifyMainValue = totalStreams;
        const last7 = streams.slice(-7);
        spotifySubValue = last7.reduce((sum, d) => sum + (d.value || 0), 0);
      } else {
        spotifyMainValue = streams.length > 0 ? (streams[streams.length - 1].value || 0) : totalStreams;
        spotifySubValue = totalStreams;
      }
    } else {
      // In TikTok view, match Spotify display to TikTok time period
      if (currentMetric.key === 'last_24h_videos' || currentMetric.key === 'last_24h_percentage') {
        if (streams.length > 0) {
          spotifyMainValue = streams[streams.length - 1].value || 0;
          spotifySubValue = totalStreams;
        } else {
          spotifyMainValue = totalStreams;
        }
      } else if (currentMetric.key === 'last_7_days_videos') {
        const last7 = streams.slice(-7);
        spotifyMainValue = last7.reduce((sum, d) => sum + (d.value || 0), 0);
        spotifySubValue = totalStreams;
      } else if (currentMetric.key === 'total_videos') {
        spotifyMainValue = totalStreams;
        const last7 = streams.slice(-7);
        spotifySubValue = last7.reduce((sum, d) => sum + (d.value || 0), 0);
      } else {
        spotifyMainValue = totalStreams;
        const last7 = streams.slice(-7);
        spotifySubValue = last7.reduce((sum, d) => sum + (d.value || 0), 0);
      }
    }
  }
  
  const rawImage = song.album_image || (song.spotify && song.spotify.album_image) || null;
  // Only use image URL if it's a valid http(s) URL — Chartex sometimes returns song titles here
  const imageUrl = (rawImage && rawImage.startsWith('http')) ? rawImage : null;
  const recordLabel = song.record_label || song.label || song.distributor || '-';
  const songId = song.id || song.chartex_song_id;
  
  // Get TikTok and Spotify IDs for analytics
  const tiktokSoundId = tiktokMetrics.sound_id || song.tiktok_sound_id || '';
  const spotifyId = (song.spotify && song.spotify.id) || song.spotify_id || '';
  
  // Debug logging for first song only
  if (index === 0) {
    console.log('Song structure for analytics:', {
      songId,
      tiktokSoundId,
      spotifyId,
      isSpotifyView,
      tiktokMainValue,
      spotifyMainValue,
      recordLabelDisplay: recordLabel,
    });
  }
  
  return `
    <tr class="song-row" 
        data-song-id="${songId || ''}" 
        data-tiktok-sound-id="${tiktokSoundId}" 
        data-spotify-id="${spotifyId}"
        style="cursor: pointer; transition: background 0.2s;" 
        onmouseover="this.style.background='#f8f9fa'" 
        onmouseout="this.style.background='white'" 
        onclick="openSongAnalytics('${songId || ''}', '${title.replace(/'/g, "\\'")}', '${artist.replace(/'/g, "\\'")}', '${tiktokSoundId}', '${spotifyId}')">
      <td style="text-align: center; font-weight: 600; color: #666;">${index + 1}</td>
      <td>
        <div class="track-info">
          ${imageUrl ? 
            `<img src="${imageUrl}" alt="${title}" class="track-image" style="width: 50px; height: 50px; border-radius: 4px; margin-right: 12px;">` :
            `<div class="track-image-placeholder" style="width: 50px; height: 50px; border-radius: 4px; margin-right: 12px; background: #3498db; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold;">${title.charAt(0)}</div>`
          }
          <div class="track-details">
            <div class="song-title" style="font-weight: 500; margin-bottom: 2px;">
              ${title}
              <div style="display: flex; gap: 8px; margin-top: 6px;">
                ${spotifyId ? `<a href="https://open.spotify.com/track/${spotifyId}" target="_blank" onclick="event.stopPropagation();" style="display: inline-flex; align-items: center; gap: 4px; padding: 4px 8px; background: #1DB954; color: white; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: 600;"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg>Spotify</a>` : ''}
                ${tiktokSoundId ? `<a href="https://www.tiktok.com/music/${tiktokSoundId}" target="_blank" onclick="event.stopPropagation();" style="display: inline-flex; align-items: center; gap: 4px; padding: 4px 8px; background: #000; color: white; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: 600;"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/></svg>TikTok</a>` : ''}
              </div>
            </div>
            <div class="song-artist" style="font-size: 13px; color: #999;">${artist}</div>
          </div>
        </div>
      </td>
      <td style="color: #666;">${recordLabel}</td>
      <td style="text-align: center;">
        <div style="font-size: 11px; color: #999; line-height: 1.3;">
          <div>${currentMetric.label24h || (isSpotifyView ? 'Daily' : '24h')}</div>
          <div>${currentMetric.labelTotal || 'Total'}</div>
        </div>
      </td>
      ${isSpotifyView ? `
      <td style="text-align: right;">
        ${spotifyMainValue > 0 ? `
          <div style="font-size: 15px; font-weight: 600; color: #2c3e50; margin-bottom: 2px;">
            ${formatNumber(spotifyMainValue)}
          </div>
          ${spotifySubValue > 0 ? `
            <div style="font-size: 11px; color: #999; margin-top: 2px;">
              ${formatNumber(spotifySubValue)}
            </div>
          ` : ''}
        ` : `<span style="color: #999;">-</span>`}
      </td>
      <td style="text-align: right;">
        <div style="font-size: 15px; font-weight: 600; color: #2c3e50; margin-bottom: 2px;">
          ${formatNumber(tiktokMainValue)}
        </div>
        <div style="font-size: 12px; color: ${tiktokPercentage >= 0 ? '#27ae60' : '#e74c3c'}; display: flex; align-items: center; justify-content: flex-end; gap: 4px;">
          ${tiktokPercentage >= 0 ? '▲' : '▼'} ${Math.abs(tiktokPercentage).toFixed(2)}%
        </div>
        <div style="font-size: 11px; color: #999; margin-top: 2px;">
          ${formatNumber(tiktokTotalValue)}
        </div>
      </td>
      ` : `
      <td style="text-align: right;">
        <div style="font-size: 15px; font-weight: 600; color: #2c3e50; margin-bottom: 2px;">
          ${formatNumber(tiktokMainValue)}${currentMetric.isPercentage ? '%' : ''}
        </div>
        <div style="font-size: 12px; color: ${tiktokPercentage >= 0 ? '#27ae60' : '#e74c3c'}; display: flex; align-items: center; justify-content: flex-end; gap: 4px;">
          ${tiktokPercentage >= 0 ? '▲' : '▼'} ${Math.abs(tiktokPercentage).toFixed(2)}%
        </div>
        <div style="font-size: 11px; color: #999; margin-top: 2px;">
          ${formatNumber(tiktokTotalValue)}
        </div>
      </td>
      <td style="text-align: right;">
        ${spotifyMainValue > 0 ? `
          <div style="font-size: 15px; font-weight: 600; color: #2c3e50; margin-bottom: 2px;">
            ${formatNumber(spotifyMainValue)}
          </div>
          ${spotifySubValue > 0 ? `
            <div style="font-size: 11px; color: #999; margin-top: 2px;">
              ${formatNumber(spotifySubValue)}
            </div>
          ` : ''}
        ` : `<span style="color: #999;">-</span>`}
      </td>
      `}
    </tr>
  `;
}

// Make generateSongRow globally available too
window.generateSongRow = generateSongRow;
