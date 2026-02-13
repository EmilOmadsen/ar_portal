# 🎵 Spotify Integration Setup Guide

## Why Spotify API?

Since your Chartmetric plan doesn't include track-level endpoints, we're integrating Spotify's Web API directly (it's **free**!) to get:

✅ **Track artwork/images** (album covers)  
✅ **Popularity scores** (0-100, correlates with streams)  
✅ **Direct Spotify & TikTok links**  
✅ **Audio features** (optional: danceability, energy, etc.)

## Step 1: Get Spotify Credentials (5 minutes)

1. **Go to Spotify Developer Dashboard**  
   👉 https://developer.spotify.com/dashboard

2. **Login with your Spotify account**  
   (Create a free account if you don't have one)

3. **Create an App**
   - Click "Create app"
   - App name: `A&R Portal Discovery`
   - App description: `Track discovery system for A&R`
   - Redirect URI: `http://localhost:8000/callback` (required but not used for our flow)
   - Check "Web API" box
   - Click "Save"

4. **Get Your Credentials**
   - Click "Settings" button
   - Copy **Client ID**
   - Click "View client secret" and copy **Client Secret**

## Step 2: Add to .env File

Open your `.env` file and add these lines:

```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

## Step 3: Enrich Your Tracks

Run the enrichment script to add images and links to your existing 17 tracks:

```bash
.venv\Scripts\python.exe enrich_with_spotify.py
```

This will:
- Search Spotify for each track
- Download album artwork URLs
- Get popularity scores (we'll use this to estimate streams)
- Add direct Spotify & TikTok links
- Update the database

**Takes ~2 minutes for 17 tracks**

## Step 4: Refresh Your Dashboard

After enrichment completes:
1. Refresh http://localhost:8000/dashboard/discover
2. You'll now see:
   - ✅ Track album artwork
   - ✅ Clickable Spotify links (opens in new tab)
   - ✅ Clickable TikTok sound links
   - ✅ Popularity-based ranking

## What You Get

### Before (TikTok only):
- Track names & artists
- TikTok post counts
- No images
- No streaming data

### After (Spotify integrated):
- 🎨 **Album artwork images**
- 🔗 **Clickable Spotify links** → Listen directly
- 🔗 **Clickable TikTok links** → View sound on TikTok
- 📊 **Popularity scores** → Estimate streaming performance
- 🎯 **Better ranking** → Combine TikTok virality with Spotify popularity

## Cross-Platform Ranking

With Spotify data, your trending algorithm now:
1. **TikTok Score** (0-50): Based on post counts
2. **Spotify Score** (0-40): Based on popularity (90+ = viral hit)
3. **Cross-Platform Bonus** (0-30): Tracks on BOTH platforms get huge boost

Tracks trending on **both TikTok AND Spotify** will rank at the top! 🚀

## Troubleshooting

**Issue**: "No Spotify data available"  
**Fix**: Make sure credentials are in `.env` and restart the server

**Issue**: "Track not found on Spotify"  
**Reason**: Some tracks may not be on Spotify (TikTok-only sounds, remixes)

**Issue**: Rate limiting  
**Fix**: The script includes 0.1s delays between requests, no action needed

## Next Steps

Once enriched, you can:
- View beautiful track cards with images
- Click to listen on Spotify instantly
- See cross-platform performance
- Use popularity as streaming proxy

Enjoy! 🎉
