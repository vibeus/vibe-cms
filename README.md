# Vibe's CMS system

## Development
1. Clone this repo.
2. `yarn install`
3. `hugo server`
4. Open your favourite browser and navigate to
   * http://localhost:1313/blog

## Replace hugo-common with local clone
If you want to update [hugo-common][1] and test on you local clone first, you can use [mod replace][2].

For example, if you cloned [hugo-common][1] in the same working directory as vibe-blog, run command below.
```
go mod edit -replace=github.com/vibeus/hugo-common=../hugo-common
```

**Do not commit local replace to master or live branches**

[1]: https://github.com/vibeus/hugo-common
[2]: https://github.com/golang/go/wiki/Modules#when-should-i-use-the-replace-directive
