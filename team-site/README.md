# Wharncliffe & Wonderland Team Hub

A single-file internal website for the Chick-fil-A Wharncliffe & Wonderland
team: upcoming events, announcements, a hiring link, and community resources.

Everything lives in `index.html` — no build step, no dependencies. Open the
file in any browser to view it.

## Editing content

Open `index.html` and scroll to the block near the bottom marked
**"EDIT YOUR CONTENT HERE"**:

- **Events** live in the `EVENTS` list. Copy an existing `{ ... },` block,
  change the month/day/title/details, and save. Delete a block to remove an
  event.
- **Announcements** work the same way in the `ANNOUNCEMENTS` list.
- **Hiring link**: search for `careers.chick-fil-a.com` and replace it with
  your store's own application link if you have one.

## Publishing it for the team

The easiest free option is **GitHub Pages**:

1. In the repository settings, open **Pages**.
2. Set the source to this branch and the `/team-site` folder (or move
   `index.html` to the repo root of a dedicated repo).
3. GitHub gives you a public URL you can share with the team.

Any static host (Netlify, Cloudflare Pages, Vercel) works the same way —
point it at this folder.
