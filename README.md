# Whitelist Censor Service

A standalone censoring service, whitelist-style. Centrally-mangaged, synchronized, offline-friendly. Only intended for personal use between projects.

# About

Todo

# Design FAQ

## Why \<question here\>?

- A majority of questions can be answered by "I wanted to do it `x` way, I _can_ do it `x` way, so I did it `x` way". It can end there, this project isn't a demonstration of my capabilities as an architect.
- If you want to seek further rationalization for some reason, read on.

## Why does the Discord bot have a lot of weird code?

- Standard boilerplate for my discord bots. You could argue a lot of it isn't needed and won't be needed.

## Why not designate a local, master 'server' and communicate locally over intranet?

- My personal servers are restarted daily, which means downtime or potential silent "failed-to-start"s.
- My personal servers are running livestreams that involve mouse+keyboard manipulation, which would make maintenance difficult and create unneccesary downtime.
- A remote server is already required for other tasks, might as well utilize it.
- Would still have to create a client in addition to the server, at best would just have less responsibilities and overhead.

## Why not directly route requests to a (central) remote HTTP server/database?

- Latency and unneccesary bandwidth.
- Public facing databases/HTTP servers are prime targets for automated fuzzing and attacks.
- There would be additional security work required both initially and over time, as maintenance.

## Why not use a VPN?

- Additional work, adds a failure point. The VPN may fail, disconnect, or land in a broken state, which would require additional work to account for, even if its unlikely to happen.

## For connecting from local client to remote server, why not use RPC or a message broker like ZeroMQ?

- I don't have enough experience in them to create a system as quickly as I would this one.
- May require authentication or additional security work.

## For connecting from \<`xyz project`\> to local censor client, why not use \<`something thats not an HTTP server`\>?

- REST requests are easy to do in any language, making it very easy for a project of any type to integrate.
- Using another protocol would require more complicated integration code in the project utilizing the censor service.

  (including websockets, which despite being used for `local client`->`remote server` communication, are not as universal and easy as HTTP)

## Why not use a delta update system instead of downloading entire files?

- Guaranteed consistency.
- I don't want to create additional work for a validation system.
- The files themselves are quite small in the grand scheme of things.

## Your solution doesn't seem very secure

Perhaps, but here are all the truths of the project, and hopefully you will agree its "secure enough" given the low time cost, both initial development and maintenance.

- The data itself is not very sensitive.
- The client is not accessible outside LAN.
- The server is fairly non-standard, both in architecture and server software (Python asyncio TCP server).
- Since the server is just a websocket server, it will not be indexed by a search engine.
- My concerns about security arise from CVE exploiters, high volume requests, or unauthorized usage. Targetted attacks, especially ones that would succeed, are unlikely and an acceptable risk.
- Security by obscurity is more than an effective primary shield for the usecases I intend for this project.

## Your solution is inefficient/against standards

- This project is a solution to an annoyance in a hobby project, I don't see a benefit to anyone if I were to use my time to make it efficient and up-to-standard.
- This project is based on a prototype I extracted from a hobby project, which was already a throwaway solution in the first place.
