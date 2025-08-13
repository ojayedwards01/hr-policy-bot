@echo off
echo =============================
echo Git Large File Cleanup Script
echo =============================
echo.
echo This script will help clean up large files from Git history
echo WARNING: This will modify your Git history!
echo.
echo Steps:
echo 1. Remove large files from Git cache
echo 2. Update .gitignore
echo 3. Commit the changes
echo 4. Push with force option
echo.
pause

echo.
echo Removing large files from Git cache...
git rm -r --cached model_cache/
git rm -r --cached src/store/
git rm -r --cached src/store_backup/

echo.
echo Make sure .gitignore has been updated...
echo.
echo Now commit the changes:
echo git add .
echo git commit -m "Remove large files and update .gitignore"
echo.
echo Then force push to overwrite remote history:
echo git push origin docker --force
echo.
echo IMPORTANT: Other collaborators will need to re-clone the repository!
echo.
pause
