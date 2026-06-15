# ewout05 Project Haste Server

**The HasteServer image used to provide a reliable, self-controlled and
self-hosted HasteServer for ewout05.**

![Discord]https://join.ewout05.com

## What is this repo?

This repo contains the source code for ewout05's HasteServer, designed to offer a reliable, 
self-controlled, and self-hosted paste server. We created ewout05's HasteServer to address 
the limitations of existing solutions. Many alternatives rely on outdated 
technologies, lack modern features, and fail to meet the expectations of today's 
developers.

ewout05's HasteServer builds on the solid foundation of the original haste-server 
by John Crepezzi. We deeply appreciate his work, which inspired us to take 
this concept further with improved code quality, modern tools, and enhanced 
functionality.

## API Documentation

We have published a Swagger UI for the API. You can access it by visiting 
/swagger-ui. Since CustomBin is serverless, this documentation is hosted 
directly through the service and doesn’t require a local setup.

## Paste lifetime

Pastes will stay for 7 days from creation. They may be removed earlier and
without notice.

## Usage

### From the [website]

Type or paste what you want to upload into the website, save it, and then copy
the URL. Send that to someone and they'll be able to view the file.

To make a new entry, click "New", or press `CTRL+N` (Windows/Linux) or `⌘+N`
(MacOS) on the keyboard.

### From the Console

#### UNIX Shell

You can use the following function to easily POST to your CustomBin instance.
It should be noted that due to POSIX restrictions and shell differences, the 
following may not work, but is guaranteed to on BaSH, Zsh, Fish, etc.

##### Prerequisites

For this to run, your system needs:

- `cat`
- [`curl`](https://github.com/curl/curl)
- [`jq`](https://github.com/stedolan/jq)

##### Script

```sh
haste() {
  curl -X POST -s -d "$(cat)" https://domain.com/documents | jq --raw-output '.key' | { read key; echo "https://domain.com/${key}"; }
}
```

##### Usage

```sh
cat something | haste
# https://custombin.example.com/1238193
```

You can even take this a step further, and cut out the last step of copying the
URL with:

**MacOS:**

```sh
cat something | haste | pbcopy
```

**Linux:**

```sh
cat something | haste | copy_command
```

You should replace `copy_command` with your clipboard of choice. This is
typically `xsel` or `xclipcopy` on systems using X11.

After running that, the output of `cat something` will show up as a URL which
has been conveniently copied to your clipboard.

#### PowerShell (Windows/Linux/MacOS)

##### Prerequisites

You have to install
[`powershell`](https://github.com/PowerShell/powershell/releases/latest) for
this script to work

##### Script

```ps1
Function haste {
  $fileContent = Get-Content -Path $args[0] -Encoding UTF8 -Raw
  $response = Invoke-RestMethod -Uri https://domain.com/documents -Method POST -ContentType 'text/plain; charset=utf-8' -Body $fileContent
  $key = $response.key

  Write-Host https://domain.com/$key
}
```

##### Usage

```ps1
haste .\path\to\file
# https://domain.com/1238193
```

## Contributors

Please make sure to read the [Contributing Guide][contributing] before making a
pull request.

Thank you to all the people who already contributed to this Project!

[contributing]:
  https://github.com/SOON/.github/blob/main/.github/CONTRIBUTING.md
[website]: https://haste.ewout05.com
