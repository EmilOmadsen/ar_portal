/**
 * Main Discover Page Logic
 * Handles song loading, filtering, and display
 */

// State management
let currentView = 'tiktok-trending';
let selectedTiktokMetric = 'tiktok_last_24_hours_video_count';  // TikTok time period
let selectedSpotifyMetric = 'daily_streams';  // Spotify metric
let selectedMinTiktoks = null;
let selectedMarket = '';
let selectedLabelType = '';
let loadedSongs = [];
let currentOffset = 0;
let isLoadingMore = false;
let hasMoreSongs = false;

// Make currentView globally available for other modules
window.currentView = currentView;

// Metric configurations for each view
const TIKTOK_METRICS = {
  'tiktok_last_24_hours_video_count': { label: '24 Hours', key: 'last_24h_videos' },
  'tiktok_last_7_days_video_count': { label: 'Last 7 Days', key: 'last_7_days_videos' },
  'tiktok_total_video_count': { label: 'All Time', key: 'total_videos' },
  'tiktok_last_24_hours_video_percentage': { label: '24h % Growth', key: 'last_24h_percentage', isPercentage: true }
};

const SPOTIFY_METRICS = {
  'daily_streams': { label: 'Daily Streams', key: 'daily_streams' },
  'weekly_streams': { label: 'Weekly Streams', key: 'weekly_streams' },
  'total_streams': { label: 'Total Streams', key: 'total_streams' }
};

// Utility: Format numbers
function formatNumber(num) {
  if (!num || num === 0) return '0';
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
}

// Make formatNumber globally available for discover-table.js
window.formatNumber = formatNumber;

// Utility: Update count display
function updateCount(count, totalAvailable = null) {
  const countElement = document.getElementById('resultsCount');
  if (countElement) {
    if (totalAvailable && totalAvailable > count) {
      countElement.textContent = `Showing ${count} of ${totalAvailable} results`;
    } else {
      countElement.textContent = `${count} result${count !== 1 ? 's' : ''}`;
    }
  }
}

// Get JWT token from URL or localStorage
function getToken() {
  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get('token') || localStorage.getItem('access_token');
  
  if (!token) {
    console.log('No token found, redirecting to login...');
    alert('Please log in to access the discovery page.');
    window.location.href = '/';
    return null;
  }
  
  localStorage.setItem('access_token', token);
  return token;
}

// Refresh data from Chartex
async function refreshData() {
  console.log('🔄 Refresh button clicked');
  const token = getToken();
  if (!token) {
    console.error('No token available');
    return;
  }
  
  const refreshBtn = document.getElementById('refreshBtn');
  if (!refreshBtn) {
    console.error('Refresh button not found');
    return;
  }
  
  const originalText = refreshBtn.innerHTML;
  
  try {
    // Show loading state
    console.log('Sending refresh request...');
    refreshBtn.innerHTML = '<svg style="animation: spin 1s linear infinite;" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M12 6v6l4 2"></path></svg> <span>Refreshing...</span>';
    refreshBtn.disabled = true;
    
    // Call the refresh endpoint
    const response = await fetch('/api/discovery/tiktok-trending/refresh-cache', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    console.log('Response status:', response.status);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Refresh response error:', errorText);
      throw new Error(`Refresh failed: ${response.statusText}`);
    }
    
    const result = await response.json();
    console.log('✅ Data refreshed:', result);
    
    // Show success message briefly
    refreshBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg> <span>Refreshed!</span>';
    
    // Reload the songs with fresh data after a short delay
    setTimeout(() => {
      console.log('Reloading songs...');
      loadedSongs = [];
      currentOffset = 0;
      loadSongs(false);
      
      setTimeout(() => {
        refreshBtn.innerHTML = originalText;
        refreshBtn.disabled = false;
      }, 1000);
    }, 500);
    
  } catch (error) {
    console.error('❌ Error refreshing data:', error);
    alert('Failed to refresh data: ' + error.message);
    refreshBtn.innerHTML = originalText;
    refreshBtn.disabled = false;
  }
}

// Make it globally available
window.refreshData = refreshData;

// Add CSS animation for spinning
const style = document.createElement('style');
style.textContent = `
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;
document.head.appendChild(style);

// Switch between views
function switchView(view) {
  currentView = view;
  window.currentView = view;  // Update global reference
  
  // Update tab styles
  document.getElementById('tiktokTrendingTab').classList.toggle('active', view === 'tiktok-trending');
  document.getElementById('spotifyTrendingTab').classList.toggle('active', view === 'spotify-trending');
  document.getElementById('creatorsTab').classList.toggle('active', view === 'creators');
  
  // Note: Keep selectedTiktokMetric and selectedSpotifyMetric separate
  // Don't reset them on tab switch - they persist across views
  
  // Update the metric filter buttons visibility
  updateMetricButtons(view);
  
  // Show/hide TikTok-specific filters
  const minTiktoksFilter = document.getElementById('minTiktoksFilter');
  if (minTiktoksFilter) {
    minTiktoksFilter.style.display = (view === 'tiktok-trending') ? 'flex' : 'none';
  }
  
  // Reset pagination and reload data
  loadedSongs = [];
  currentOffset = 0;
  
  // Load appropriate data based on view
  if (view === 'creators') {
    loadCreators(false);
  } else {
    loadSongs(false);
  }
}

// Update metric filter buttons based on current view
function updateMetricButtons(view) {
  // Target only the sort-by filter-buttons container (the first one inside filtersContent)
  const metricContainer = document.querySelector('#filtersContent .filters-row:first-child .filter-buttons');
  if (!metricContainer) return;
  
  if (view === 'spotify-trending') {
    // Show Spotify metric buttons
    metricContainer.innerHTML = `
      <button class="filter-btn ${selectedSpotifyMetric === 'daily_streams' ? 'active' : ''}" data-metric="daily_streams">Daily Streams</button>
      <button class="filter-btn ${selectedSpotifyMetric === 'weekly_streams' ? 'active' : ''}" data-metric="weekly_streams">Weekly Streams</button>
      <button class="filter-btn ${selectedSpotifyMetric === 'total_streams' ? 'active' : ''}" data-metric="total_streams">Total Streams</button>
    `;
  } else if (view === 'creators') {
    // Show creator sort buttons
    metricContainer.innerHTML = `
      <button class="filter-btn active" data-metric="total_followers">Total Followers</button>
      <button class="filter-btn" data-metric="last_7_days_followers_count">7-Day Growth</button>
    `;
  } else {
    // Show TikTok metric buttons
    metricContainer.innerHTML = `
      <button class="filter-btn ${selectedTiktokMetric === 'tiktok_last_24_hours_video_percentage' ? 'active' : ''}" data-metric="tiktok_last_24_hours_video_percentage">24h % Growth</button>
      <button class="filter-btn ${selectedTiktokMetric === 'tiktok_last_24_hours_video_count' ? 'active' : ''}" data-metric="tiktok_last_24_hours_video_count">24 Hours</button>
      <button class="filter-btn ${selectedTiktokMetric === 'tiktok_last_7_days_video_count' ? 'active' : ''}" data-metric="tiktok_last_7_days_video_count">Last 7 Days</button>
      <button class="filter-btn ${selectedTiktokMetric === 'tiktok_total_video_count' ? 'active' : ''}" data-metric="tiktok_total_video_count">All Time</button>
    `;
  }
  
  // Re-attach click handlers to new buttons
  attachMetricButtonHandlers();
}

// Attach event handlers to metric buttons
function attachMetricButtonHandlers() {
  // Only attach to sort-by metric buttons, NOT label-type buttons
  const sortContainer = document.querySelector('#filtersContent .filters-row:first-child .filter-buttons');
  if (!sortContainer) return;
  sortContainer.querySelectorAll('.filter-btn[data-metric]').forEach(btn => {
    btn.addEventListener('click', function() {
      const clickedMetric = this.dataset.metric;
      console.log('🎯 Metric filter clicked:', clickedMetric);
      console.log('🎯 Current view:', currentView);
      console.log('🎯 Before update - selectedTiktokMetric:', selectedTiktokMetric);
      
      sortContainer.querySelectorAll('.filter-btn[data-metric]').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      
      // Update the correct metric variable based on current view
      if (currentView === 'spotify-trending') {
        selectedSpotifyMetric = clickedMetric;
        console.log('🎯 Updated selectedSpotifyMetric to:', selectedSpotifyMetric);
      } else if (currentView === 'creators') {
        selectedCreatorSort = clickedMetric;
        console.log('🎯 Updated selectedCreatorSort to:', selectedCreatorSort);
      } else {
        selectedTiktokMetric = clickedMetric;
        console.log('🎯 Updated selectedTiktokMetric to:', selectedTiktokMetric);
      }
      
      loadedSongs = [];
      loadedCreators = [];
      currentOffset = 0;
      
      // Load appropriate data
      if (currentView === 'creators') {
        loadCreators(false);
      } else {
        loadSongs(false);
      }
    });
  });
}

// Load songs from API
async function loadSongs(append = false) {
  const container = document.getElementById('resultsContent');
  
  // If not appending, show loading and reset
  if (!append) {
    // Show more specific loading message if label filter is active
    const loadingMessage = selectedLabelType 
      ? `Loading ${selectedLabelType === 'major' ? 'Universal' : selectedLabelType.charAt(0).toUpperCase() + selectedLabelType.slice(1)} tracks...`
      : 'Loading trending content...';
    
    container.innerHTML = `
      <div class="loading">
        <div class="spinner"></div>
        <p>${loadingMessage}</p>
        ${selectedLabelType ? '<p style="font-size: 0.9em; opacity: 0.7; margin-top: 5px;">Filtering from larger dataset...</p>' : ''}
      </div>
    `;
    loadedSongs = [];
    currentOffset = 0;
    hasMoreSongs = false;
  } else {
    // Show loading indicator at bottom for "load more"
    if (isLoadingMore) return; // Prevent multiple loads
    isLoadingMore = true;
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if (loadMoreBtn) {
      loadMoreBtn.innerHTML = '<div class="spinner" style="width: 20px; height: 20px; margin: 0 auto;"></div>';
      loadMoreBtn.disabled = true;
    }
  }
  
  const token = getToken();
  if (!token) return;
  
  try {
    const searchTerm = document.getElementById('searchInput').value;
    
    let response;
    
    if (currentView === 'tiktok-trending') {
      // Load TikTok trending data from Chartex API
      console.log('🔧 Building TikTok params with selectedTiktokMetric:', selectedTiktokMetric);
      
      const params = new URLSearchParams({
        sort_by: selectedTiktokMetric,  // Use TikTok time period filter
        limit: 10,  // Load 10 songs at a time for faster loading
        include_history: true,
        history_days: 3,  // Reduced from 7 to 3 for faster loading
        include_spotify_metadata: false  // Skip Spotify metadata for faster loading
      });
      
      // Add offset for pagination when loading more
      if (append && currentOffset > 0) {
        params.set('offset', currentOffset);
      }
      
      if (selectedMinTiktoks) {
        params.append('min_video_count', selectedMinTiktoks);
      }
      
      if (selectedMarket) {
        params.append('country_code', selectedMarket);
      }
      
      if (selectedLabelType) {
        params.append('label_type', selectedLabelType);
      }
      
      if (searchTerm) {
        params.append('search', searchTerm);
      }
      
      console.log('Fetching TikTok trending with params:', params.toString());
      
      // Add timestamp to prevent browser caching
      params.append('_t', Date.now());
      
      response = await fetch(`/api/discovery/tiktok-trending/songs?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache'
        },
        cache: 'no-store'  // Prevent browser from caching this request
      });
    } else if (currentView === 'spotify-trending') {
      // Load Spotify trending data - sorted by Spotify streaming metrics
      const params = new URLSearchParams({
        sort_by: 'spotify_streams',  // Sort by Spotify streaming data
        tiktok_metric: selectedTiktokMetric,  // Use TikTok time period for initial Chartex fetch
        spotify_sort_metric: selectedSpotifyMetric,  // daily_streams, weekly_streams, total_streams
        limit: 10,  // Load 10 songs at a time for faster loading
        include_history: true,
        history_days: 3,  // Reduced from 7 to 3 for faster loading
        include_spotify_metadata: true  // Need Spotify data for this view
      });
      
      // Add offset for pagination when loading more
      if (append && currentOffset > 0) {
        params.set('offset', currentOffset);
      }
      
      if (selectedMarket) {
        params.append('country_code', selectedMarket);
      }
      
      if (selectedLabelType) {
        params.append('label_type', selectedLabelType);
      }
      
      if (searchTerm) {
        params.append('search', searchTerm);
      }
      
      console.log('Fetching Spotify trending with params:', params.toString());
      
      // Add timestamp to prevent browser caching
      params.append('_t', Date.now());
      
      response = await fetch(`/api/discovery/tiktok-trending/songs?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache'
        },
        cache: 'no-store'
      });
    } else {
      // Fallback  view
      response = null;
    }
    
    // Handle response
    if (response) {
      if (response.ok) {
        const data = await response.json();
        console.log('API Response:', data);
        console.log('Songs array:', data.songs);
        console.log('Songs length:', data.songs?.length);
        console.log('First song example:', data.songs?.[0]);
        console.log('🔍 has_more flag:', data.has_more);
        console.log('🔍 Total available:', data.total_available);
        console.log('🔍 Current offset:', data.offset);
        console.log('🔍 Limit:', data.limit);
        console.log('🔍 Total returned:', data.total);
        
        // Log the sort order for debugging
        if (data.songs?.length >= 3) {
          console.log('📊 First 3 songs metric values for', selectedTiktokMetric, ':');
          data.songs.slice(0, 3).forEach((song, i) => {
            const metrics = song.tiktok_metrics || {};
            console.log(`  ${i+1}. ${song.title}: `, {
              last_24h: metrics.last_24h_videos,
              last_7d: metrics.last_7_days_videos, 
              total: metrics.total_videos,
              percentage: metrics.last_24h_percentage
            });
          });
        }
        
        if (data.songs && data.songs.length > 0) {
          // Add new songs to loaded list
          loadedSongs = append ? [...loadedSongs, ...data.songs] : data.songs;
          currentOffset = loadedSongs.length;
          hasMoreSongs = data.has_more || false;
          
          console.log('🔍 hasMoreSongs set to:', hasMoreSongs);
          
          // Display all loaded songs
          displayResults(loadedSongs);
          
          // Update count - show total available for label filters
          const displayCount = data.total_available || loadedSongs.length;
          updateCount(loadedSongs.length, displayCount);
          
          // Add "Load More" button if there are more songs available
          if (hasMoreSongs) {
            console.log('✅ Calling addLoadMoreButton()');
            addLoadMoreButton();
          } else {
            console.log('❌ NOT adding load more button - hasMoreSongs is false');
            // Remove load more button if no more songs
            const existingBtn = document.getElementById('loadMoreBtn');
            if (existingBtn) existingBtn.remove();
          }
        } else {
          if (!append) {
            container.innerHTML = '<div class="no-results">No songs found matching your criteria.</div>';
          } else {
            // No more songs to load
            const existingBtn = document.getElementById('loadMoreBtn');
            if (existingBtn) existingBtn.remove();
          }
        }
      } else if (response.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('access_token');
        alert('Your session has expired. Please log in again.');
        window.location.href = '/';
        return;
      } else {
        throw new Error('Failed to fetch songs');
      }
    } else {
      // No response - shouldn't happen
      container.innerHTML = '<div class="no-results">View not configured</div>';
    }
  } catch (error) {
    console.error('Error loading songs:', error);
    if (!append) {
      container.innerHTML = `
        <div class="error-message">
          <p>Failed to load songs. Please try again.</p>
          <button onclick="loadSongs(false)" class="action-btn">Retry</button>
        </div>
      `;
    }
  } finally {
    isLoadingMore = false;
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if (loadMoreBtn) {
      loadMoreBtn.innerHTML = 'Load More Songs';
      loadMoreBtn.disabled = false;
    }
  }
}

// Load creators from API
let loadedCreators = [];
let selectedCreatorSort = 'total_followers';

async function loadCreators(append = false) {
  const container = document.getElementById('resultsContent');
  
  // If not appending, show loading and reset
  if (!append) {
    loadedCreators = [];
    currentOffset = 0;
    container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div> Loading creators...</div>';
  } else {
    isLoadingMore = true;
  }
  
  try {
    const token = localStorage.getItem('access_token');
    if (!token) {
      window.location.href = '/';
      return;
    }
    
    const searchTerm = document.getElementById('searchInput')?.value?.trim();
    
    const params = new URLSearchParams({
      sort_by: selectedCreatorSort,
      limit: 15,
    });
    
    // Add offset for pagination
    if (append && currentOffset > 0) {
      params.set('offset', currentOffset);
    }
    
    if (selectedMarket) {
      params.append('country_code', selectedMarket);
    }
    
    if (searchTerm) {
      params.append('search', searchTerm);
    }
    
    // Add cache-busting
    params.append('_t', Date.now());
    
    console.log('Fetching creators with params:', params.toString());
    
    const response = await fetch(`/api/discovery/creators/list?${params}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache'
      },
      cache: 'no-store'
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('Creators API Response:', data);
      
      if (data.creators && data.creators.length > 0) {
        loadedCreators = append ? [...loadedCreators, ...data.creators] : data.creators;
        currentOffset = loadedCreators.length;
        hasMoreSongs = data.has_more || false;  // Reuse hasMoreSongs variable
        
        displayCreators(loadedCreators);
        updateCount(loadedCreators.length, data.total);
        
        // Add load more button if more creators available
        if (hasMoreSongs) {
          addLoadMoreButtonForCreators();
        } else {
          const existingBtn = document.getElementById('loadMoreBtn');
          if (existingBtn) existingBtn.remove();
        }
      } else {
        if (!append) {
          container.innerHTML = '<div class="no-results">No creators found matching your criteria.</div>';
        } else {
          const existingBtn = document.getElementById('loadMoreBtn');
          if (existingBtn) existingBtn.remove();
        }
      }
    } else if (response.status === 401) {
      localStorage.removeItem('access_token');
      alert('Your session has expired. Please log in again.');
      window.location.href = '/';
      return;
    } else {
      throw new Error('Failed to fetch creators');
    }
  } catch (error) {
    console.error('Error loading creators:', error);
    if (!append) {
      container.innerHTML = `
        <div class="error-message">
          <p>Failed to load creators. Please try again.</p>
          <button onclick="loadCreators(false)" class="action-btn">Retry</button>
        </div>
      `;
    }
  } finally {
    isLoadingMore = false;
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if (loadMoreBtn) {
      loadMoreBtn.innerHTML = 'Load More Creators';
      loadMoreBtn.disabled = false;
    }
  }
}

// Display creators in table format
function displayCreators(creators) {
  const container = document.getElementById('resultsContent');
  
  let html = `
    <table class="songs-table">
      <thead>
        <tr>
          <th style="width: 60px">#</th>
          <th style="width: 80px">Avatar</th>
          <th>Creator</th>
          <th style="text-align: right">Followers</th>
          <th style="text-align: right">7-Day Growth</th>
          <th style="text-align: right">Total Videos</th>
          <th style="width: 120px; text-align: center">Actions</th>
        </tr>
      </thead>
      <tbody>
  `;
  
  creators.forEach((creator, index) => {
    const metadata = creator.metadata || creator;
    const username = metadata.username || 'Unknown';
    const displayName = metadata.display_name || username;
    const avatarUrl = metadata.avatar_url || metadata.avatar_thumbnail || '';
    const followers = metadata.total_followers || 0;
    const growth = creator.last_7_days_followers_count || metadata.last_7_days_followers_count || 0;
    const totalVideos = metadata.total_videos || 0;
    const verified = metadata.verified || false;
    
    // Get first letter for fallback
    const initial = (displayName || username || '?').charAt(0).toUpperCase();
    
    html += `
      <tr class="song-row" onclick="viewCreatorAnalytics('${username}')">
        <td>${index + 1}</td>
        <td>
          ${avatarUrl ? 
            `<img src="${avatarUrl}" alt="${displayName}" 
              style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover;" 
              onerror="this.style.display='none'; this.nextSibling.style.display='flex';">
             <div style="display: none; width: 50px; height: 50px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px;">${initial}</div>` 
            : 
            `<div style="width: 50px; height: 50px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px;">${initial}</div>`
          }
        </td>
        <td>
          <div style="display: flex; flex-direction: column;">
            <strong>@${username}</strong>
            <span style="font-size: 12px; color: #888;">${displayName}${verified ? ' ✓' : ''}</span>
          </div>
        </td>
        <td style="text-align: right"><strong>${formatNumber(followers)}</strong></td>
        <td style="text-align: right; color: ${growth > 0 ? '#2ecc71' : '#888'}">
          ${growth > 0 ? '+' : ''}${formatNumber(growth)}
        </td>
        <td style="text-align: right">${formatNumber(totalVideos)}</td>
        <td style="text-align: center">
          <button class="action-btn" onclick="event.stopPropagation(); viewCreatorAnalytics('${username}')">
            View Analytics
          </button>
        </td>
      </tr>
    `;
  });
  
  html += `
      </tbody>
    </table>
  `;
  
  container.innerHTML = html;
}

// Add load more button for creators
function addLoadMoreButtonForCreators() {
  const container = document.getElementById('resultsContent');
  const existingBtn = document.getElementById('loadMoreBtn');
  if (existingBtn) existingBtn.remove();
  
  const btnContainer = document.createElement('div');
  btnContainer.id = 'loadMoreBtnContainer';
  btnContainer.style.cssText = 'text-align: center; padding: 30px 0; margin-top: 20px;';
  btnContainer.innerHTML = `
    <button id="loadMoreBtn" style="
      background: #3498db;
      color: white;
      border: none;
      padding: 14px 40px;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      box-shadow: 0 2px 4px rgba(52, 152, 219, 0.3);
      font-family: 'Univers 55', sans-serif;
    ">
      Load More Creators
    </button>
  `;
  
  container.appendChild(btnContainer);
  
  document.getElementById('loadMoreBtn').addEventListener('click', () => {
    loadCreators(true);
  });
  
  const btn = document.getElementById('loadMoreBtn');
  btn.addEventListener('mouseenter', () => {
    btn.style.background = '#2980b9';
    btn.style.transform = 'translateY(-2px)';
    btn.style.boxShadow = '0 4px 8px rgba(52, 152, 219, 0.4)';
  });
  btn.addEventListener('mouseleave', () => {
    btn.style.background = '#3498db';
    btn.style.transform = 'translateY(0)';
    btn.style.boxShadow = '0 2px 4px rgba(52, 152, 219, 0.3)';
  });
}

// Navigate to creator analytics page
function viewCreatorAnalytics(username) {
  window.location.href = `/dashboard/creator-analytics?username=${encodeURIComponent(username)}`;
}

// Add "Load More" button to the results
function addLoadMoreButton() {
  const container = document.getElementById('resultsContent');
  
  // Remove existing button and container if present
  const existingContainer = document.getElementById('loadMoreBtnContainer');
  if (existingContainer) existingContainer.remove();
  const existingBtn = document.getElementById('loadMoreBtn');
  if (existingBtn) existingBtn.remove();
  
  // Create new button
  const btnContainer = document.createElement('div');
  btnContainer.id = 'loadMoreBtnContainer';
  btnContainer.style.cssText = 'text-align: center; padding: 30px 0; margin-top: 20px;';
  btnContainer.innerHTML = `
    <button id="loadMoreBtn" style="
      background: #3498db;
      color: white;
      border: none;
      padding: 14px 40px;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      box-shadow: 0 2px 4px rgba(52, 152, 219, 0.3);
      font-family: 'Univers 55', sans-serif;
    ">
      Load More Songs
    </button>
  `;
  
  container.appendChild(btnContainer);
  
  // Add click handler
  document.getElementById('loadMoreBtn').addEventListener('click', () => {
    loadSongs(true); // Load more with append=true
  });
  
  // Add hover effect
  const btn = document.getElementById('loadMoreBtn');
  btn.addEventListener('mouseenter', () => {
    btn.style.background = '#2980b9';
    btn.style.transform = 'translateY(-2px)';
    btn.style.boxShadow = '0 4px 8px rgba(52, 152, 219, 0.4)';
  });
  btn.addEventListener('mouseleave', () => {
    btn.style.background = '#3498db';
    btn.style.transform = 'translateY(0)';
    btn.style.boxShadow = '0 2px 4px rgba(52, 152, 219, 0.3)';
  });
}

// Navigate to song analytics page
function openSongAnalytics(songId, title, artist, tiktokSoundId, spotifyId) {
  // Determine which platform to use - prioritize based on data availability
  let platform = 'spotify';
  let id = spotifyId;
  
  // If no Spotify ID but we have TikTok ID, use TikTok
  if (!spotifyId && tiktokSoundId) {
    platform = 'tiktok';
    id = tiktokSoundId;
  }
  
  if (!id) {
    alert('No analytics available for this song');
    return;
  }
  
  // Navigate to song analytics with platform and ID
  const params = new URLSearchParams({
    platform: platform,
    id: id,
    title: title,
    artist: artist
  });
  
  window.location.href = `/dashboard/song-analytics?${params.toString()}`;
}

// Make it globally available
window.openSongAnalytics = openSongAnalytics;

// Display results in table format
function displayResults(songs) {
  const container = document.getElementById('resultsContent');
  
  if (songs.length === 0) {
    container.innerHTML = '<p style="text-align: center; color: #7f8c8d;">No results found</p>';
    return;
  }

  try {
    console.log('🎨 Starting displayResults with', songs.length, 'songs');
    console.log('🎨 Current view:', currentView);
    console.log('🎨 Selected TikTok metric:', selectedTiktokMetric);
    console.log('🎨 Selected Spotify metric:', selectedSpotifyMetric);
    
    // Get selected metric information based on current view
    const metricMapping = {
      'tiktok_last_24_hours_video_percentage': { key: 'last_24h_percentage', label24h: '24h', label7d: '24h %', labelTotal: '24h %', isPercentage: true },
      'tiktok_last_24_hours_video_count': { key: 'last_24h_videos', label24h: '24h', label7d: '24h', labelTotal: 'Total', isPercentage: false },
      'tiktok_last_7_days_video_count': { key: 'last_7_days_videos', label24h: '24h', label7d: '7d', labelTotal: 'Total', isPercentage: false },
      'tiktok_total_video_count': { key: 'total_videos', label24h: '24h', label7d: '7d', labelTotal: 'Total', isPercentage: false },
      'daily_streams': { key: 'daily_streams', label24h: 'Daily', label7d: 'Daily', labelTotal: 'Total', isPercentage: false },
      'weekly_streams': { key: 'weekly_streams', label24h: 'Weekly', label7d: 'Weekly', labelTotal: 'Total', isPercentage: false },
      'total_streams': { key: 'total_streams', label24h: 'Total', label7d: 'Total', labelTotal: 'All Time', isPercentage: false }
    };

    // Use correct metric variable based on current view
    const selectedMetric = currentView === 'spotify-trending' ? selectedSpotifyMetric : selectedTiktokMetric;
    const currentMetric = metricMapping[selectedMetric] || metricMapping['tiktok_last_24_hours_video_count'];
    
    console.log('🎨 Using metric:', selectedMetric, currentMetric);

    const tableHTML = generateTableHTML(songs, currentMetric);
    console.log('🎨 Generated table HTML length:', tableHTML.length);
    
    container.innerHTML = tableHTML;
    console.log('✅ Table displayed successfully');
  } catch (error) {
    console.error('❌ Error in displayResults:', error);
    console.error('Error stack:', error.stack);
    container.innerHTML = `
      <div class="error-message">
        <p>Error displaying results: ${error.message}</p>
        <button onclick="loadSongs(false)" class="action-btn">Retry</button>
      </div>
    `;
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOM loaded, initializing discover page...');
  
  // Setup filter toggle button
  const filtersToggleBtn = document.getElementById('filtersToggle');
  if (filtersToggleBtn) {
    filtersToggleBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      const content = document.getElementById('filtersContent');
      const marketContent = document.getElementById('marketDropdownContent');
      const arrow = document.getElementById('filtersArrow');
      
      if (content) {
        // Close market dropdown if open
        if (marketContent) {
          marketContent.style.display = 'none';
          const marketArrow = document.querySelector('#marketDropdown span:last-child');
          if (marketArrow) marketArrow.textContent = '▼';
        }
        
        // Toggle filters using computed style
        const computedStyle = window.getComputedStyle(content);
        const isVisible = computedStyle.display === 'block';
        content.style.display = isVisible ? 'none' : 'block';
        if (arrow) arrow.textContent = isVisible ? '▼' : '▲';
        console.log('Filters toggled:', isVisible ? 'closed' : 'opened');
      }
    });
  } else {
    console.error('filtersToggle button not found!');
  }
  
  // Market dropdown toggle
  const marketDropdownBtn = document.getElementById('marketDropdown');
  if (marketDropdownBtn) {
    marketDropdownBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      const content = document.getElementById('marketDropdownContent');
      const filtersContent = document.getElementById('filtersContent');
      const arrow = document.querySelector('#marketDropdown span:last-child');
      
      if (content) {
        // Close filters dropdown if open
        if (filtersContent) {
          filtersContent.style.display = 'none';
          const filtersArrow = document.getElementById('filtersArrow');
          if (filtersArrow) filtersArrow.textContent = '▼';
        }
        
        // Toggle market dropdown using computed style
        const computedStyle = window.getComputedStyle(content);
        const isVisible = computedStyle.display === 'block';
        content.style.display = isVisible ? 'none' : 'block';
        if (arrow) arrow.textContent = isVisible ? '▼' : '▲';
        console.log('Market dropdown toggled:', isVisible ? 'closed' : 'opened');
      }
    });
  }
  
  // Close dropdowns when clicking outside
  document.addEventListener('click', function(e) {
    // Don't close when clicking inside the filter panels, market dropdown, or the toggle buttons themselves
    if (!e.target.closest('.filters-dropdown') && !e.target.closest('#filtersContent') && !e.target.closest('.market-dropdown-wrapper') && !e.target.closest('.market-dropdown') && !e.target.closest('#filtersToggle')) {
      const filtersContent = document.getElementById('filtersContent');
      const marketContent = document.getElementById('marketDropdownContent');
      const filtersArrow = document.getElementById('filtersArrow');
      const marketArrow = document.querySelector('#marketDropdown span:last-child');
      
      if (filtersContent) filtersContent.style.display = 'none';
      if (marketContent) marketContent.style.display = 'none';
      if (filtersArrow) filtersArrow.textContent = '▼';
      if (marketArrow) marketArrow.textContent = '▼';
    }
  });
  
  // Country flags mapping
  const countryFlags = {
    'US': '🇺🇸', 'GB': '🇬🇧', 'DE': '🇩🇪', 'FR': '🇫🇷', 'ES': '🇪🇸', 'IT': '🇮🇹', 
    'BR': '🇧🇷', 'MX': '🇲🇽', 'CA': '🇨🇦', 'AU': '🇦🇺', 'JP': '🇯🇵', 'KR': '🇰🇷',
    'IN': '🇮🇳', 'CN': '🇨🇳', 'SE': '🇸🇪', 'NO': '🇳🇴', 'DK': '🇩🇰', 'FI': '🇫🇮',
    'NL': '🇳🇱', 'BE': '🇧🇪', 'CH': '🇨🇭', 'AT': '🇦🇹', 'PL': '🇵🇱', 'TR': '🇹🇷',
    'RU': '🇷🇺', 'AR': '🇦🇷', 'CL': '🇨🇱', 'CO': '🇨🇴', 'PE': '🇵🇪', 'ZA': '🇿🇦',
    'NZ': '🇳🇿', 'IE': '🇮🇪', 'PT': '🇵🇹', 'GR': '🇬🇷', 'CZ': '🇨🇿', 'HU': '🇭🇺',
    'RO': '🇷🇴', 'UA': '🇺🇦', 'IL': '🇮🇱', 'TH': '🇹🇭', 'PH': '🇵🇭', 'MY': '🇲🇾',
    'SG': '🇸🇬', 'ID': '🇮🇩', 'VN': '🇻🇳', 'AE': '🇦🇪', 'SA': '🇸🇦', 'EG': '🇪🇬',
    'NG': '🇳🇬', 'KE': '🇰🇪', 'PK': '🇵🇰', 'BD': '🇧🇩', 'HK': '🇭🇰', 'TW': '🇹🇼'
  };
  
  // Market option selection handlers
  const marketOptions = document.querySelectorAll('.market-option');
  marketOptions.forEach(option => {
    option.addEventListener('click', function() {
      const value = this.dataset.value;
      const label = this.dataset.label;
      const flag = value ? (countryFlags[value] || '🌐') : '🌍';
      
      console.log('Market selected:', label, 'Code:', value, 'Flag:', flag);
      
      // Update selected state
      marketOptions.forEach(opt => {
        opt.classList.remove('active');
        opt.style.background = 'white';
      });
      this.classList.add('active');
      this.style.background = '#f8f9fa';
      
      // Update display with flag emoji
      const selectedMarketSpan = document.getElementById('selectedMarket');
      const selectedMarketEmoji = document.getElementById('selectedMarketEmoji');
      if (selectedMarketSpan) {
        selectedMarketSpan.textContent = label;
      }
      if (selectedMarketEmoji) {
        selectedMarketEmoji.textContent = flag;
      }
      
      // Close dropdown
      const marketContent = document.getElementById('marketDropdownContent');
      if (marketContent) marketContent.style.display = 'none';
      const arrow = document.querySelector('#marketDropdown span:last-child');
      if (arrow) arrow.textContent = '▼';
      
      // Update selected market and reload
      selectedMarket = value;
      loadedSongs = [];
      currentOffset = 0;
      loadSongs(false);
    });
    
    // Add hover effect
    option.addEventListener('mouseenter', function() {
      this.style.background = '#f8f9fa';
    });
    option.addEventListener('mouseleave', function() {
      if (!this.classList.contains('active')) {
        this.style.background = 'white';
      }
    });
  });
  
  // Market search functionality
  const marketSearchInput = document.getElementById('marketSearch');
  if (marketSearchInput) {
    marketSearchInput.addEventListener('input', function() {
      const searchTerm = this.value.toLowerCase();
      const marketOptions = document.querySelectorAll('.market-option');
      
      marketOptions.forEach(option => {
        const label = option.dataset.label ? option.dataset.label.toLowerCase() : '';
        const code = option.dataset.value ? option.dataset.value.toLowerCase() : '';
        
        if (label.includes(searchTerm) || code.includes(searchTerm)) {
          option.style.display = 'flex';
        } else {
          option.style.display = 'none';
        }
      });
    });
  }
  
  // Min TikToks filter buttons
  document.querySelectorAll('.min-tiktok-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      console.log('Min TikToks filter clicked:', this.dataset.value);
      document.querySelectorAll('.min-tiktok-btn').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      selectedMinTiktoks = parseInt(this.dataset.value);
      const customInput = document.getElementById('customMinTiktoks');
      if (customInput) customInput.value = '';
      loadedSongs = [];
      currentOffset = 0;
      loadSongs(false);
    });
  });

  // Custom min TikToks input
  const customMinInput = document.getElementById('customMinTiktoks');
  if (customMinInput) {
    customMinInput.addEventListener('change', function() {
      if (this.value) {
        console.log('Custom min TikToks entered:', this.value);
        document.querySelectorAll('.min-tiktok-btn').forEach(b => b.classList.remove('active'));
        selectedMinTiktoks = parseInt(this.value);
        loadedSongs = [];
        currentOffset = 0;
        loadSongs(false);
      }
    });
  }

  // Label Type filter buttons
  document.querySelectorAll('.label-type-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      console.log('Label type filter clicked:', this.dataset.value);
      document.querySelectorAll('.label-type-btn').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      selectedLabelType = this.dataset.value;
      loadedSongs = [];
      currentOffset = 0;
      loadSongs(false);
    });
  });

  // Search input with debounce
  let searchTimeout;
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('input', function() {
      console.log('Search input:', this.value);
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        loadedSongs = [];
        currentOffset = 0;
        loadSongs(false);
      }, 500);
    });
  }
  
  console.log('All filter event handlers initialized');
  
  // Attach metric button handlers for initial load
  attachMetricButtonHandlers();
  
  // Load initial songs
  loadSongs();
});
