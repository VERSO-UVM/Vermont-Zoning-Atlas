# Migration from Jekyll to Static HTML

This site has been converted from a Jekyll-based site to a pure static HTML site. All pages have been converted to HTML with a custom CSS stylesheet.

## What Changed

### New Files
- `index.html` - Static homepage with refactored JavaScript (eliminates 11 repetitive fetch blocks)
- `about.html` - About page
- `data.html` - Data documentation page
- `contribute.html` - Contribution guidelines with glossary
- `resources.html` - Resources and visualizations
- `404.html` - Updated error page (no longer uses Jekyll layout)
- `styles.css` - Custom stylesheet (replaces Minima theme)
- `.nojekyll` - Tells GitHub Pages to skip Jekyll processing

### Updated Files
- `.github/workflows/jekyll.yml` - Simplified to deploy static files only (no Ruby/Jekyll build)

### Files You Can Keep or Remove

**Safe to Remove** (no longer needed for the static site):
- `Gemfile` - Ruby dependencies
- `Gemfile.lock` - Ruby dependency lock file
- `minima.gemspec` - Jekyll theme specification
- `_config.yml` - Jekyll configuration
- `*.md` files in root (index.md, about.md, data.md, contribute.md, resources.md) - Replaced by .html versions

**Keep for Reference** (useful documentation):
- `README.md` - Project documentation
- `Bylaw Links.md` - Reference table of jurisdiction links
- `Updating a Jurisdiction.md` - GIS workflow documentation
- `.gitignore` - Still useful for ignoring OS and build files

**Keep as Data/Content**:
- `data/` folder - All GeoJSON data files
- `assets/` folder - Images and other assets
- `LICENSE` - Project license
- `analysis/` and `training/` folders - Project documentation

## Benefits of Static HTML

1. **Faster deployment** - No Ruby/Jekyll build process
2. **Simpler maintenance** - No Ruby dependencies to manage
3. **Lighter weight** - Direct HTML serving
4. **Better JavaScript control** - Refactored map loading code
5. **No build errors** - No compilation, just plain HTML/CSS/JS

## Testing the Site

You can test the site locally by opening `index.html` in your browser. However, the map won't load properly due to CORS restrictions when opening from `file://`. 

To test properly:
```bash
# Using Python
python3 -m http.server 8000

# Using Node.js
npx http-server

# Using PHP
php -S localhost:8000
```

Then visit `http://localhost:8000` in your browser.

## Deployment

The site will automatically deploy to GitHub Pages when pushed to the `main` branch. The GitHub Actions workflow handles the deployment.

## Reverting to Jekyll

If you need to revert to Jekyll, you can:
1. Restore the old workflow file
2. Use the `.md` files instead of `.html` files
3. Remove `.nojekyll` file
4. Run `bundle install` and `bundle exec jekyll serve`

The old `.md` files are still in the repository for reference.
