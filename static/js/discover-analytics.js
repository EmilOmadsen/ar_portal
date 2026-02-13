/**
 * Song Analytics - Navigate to Dedicated Page
 */

window.openSongAnalytics = function(songId, title, artist, tiktokSoundId, spotifyId) {
  console.log('openSongAnalytics called with:', { songId, title, artist, tiktokSoundId, spotifyId });
  
  if (!songId || songId === 'undefined' || songId === 'null') {
    alert('Song ID is missing. Cannot load analytics.');
    console.error('Invalid song ID:', songId);
    return;
  }
  
  const params = new URLSearchParams({
    id: songId,
    token: localStorage.getItem('access_token') || localStorage.getItem('token')
  });
  
  if (title) params.append('title', title);
  if (artist) params.append('artist', artist);
  if (tiktokSoundId) params.append('tiktok_sound_id', tiktokSoundId);
  if (spotifyId) params.append('spotify_id', spotifyId);
  
  window.location.href = `/dashboard/song-analytics?${params.toString()}`;
};

// Close analytics modal function (needed by HTML onclick handler)
window.closeAnalyticsModal = function() {
  const modal = document.getElementById('analyticsModal');
  if (modal) {
    modal.classList.remove('active');
  }
};

console.log('discover-analytics.js loaded');
