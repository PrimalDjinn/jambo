---
layout: home

hero:
  name: "Jambo Docs for"
  text: "Customer Management REST API"
  tagline: All codebases eventually become append only
  actions:
    - theme: brand
      text: ⌚ Quickstart
      link: ./api/quickstart.md
    - theme: alt
      text: 📄Docs
      link: /api/installation      
  

features:
  - title: PostMan 👩‍🚀
    details: Download the PostMan Collection here
    link: 
  - title: Redis 🫙
    details: This project leverages the power of Redis for caching. Used version 7.2, as it's the last open source one.
    link: https://pypi.org/project/django-redis/
  - title: Postgres 🐘
    details: Used, Postres for database, literally plug and play due to django's powerful ORM
    link: https://docs.djangoproject.com/en/5.0/topics/db/queries/
  - title: NginX 🔃
    details: I placed the API server behind a proxy in Docker, this in theory should allow load balancing and serve static files
    link: https://nginx.org/en/
  - title: ULID 🔢
    details: Instead of the popular UUID, this project uses lexographically ordered random tokens. This is to help quicken insertion and deletion of values in the db.
    link: https://github.com/ahawker/django-ulid
  - title: Data Protection ⚖️
    details: This app has been built with the requirements of DPA, 2019 and provides endpoints for users to edit and delete their data
    link: http://kenyalaw.org:8181/exist/rest//db/kenyalex/Kenya/Legislation/English/Acts%20and%20Regulations/D/Data%20Protection%20Act%20-%20No.%2024%20of%202019/docs/DataProtectionAct24of2019.pdf
  - title: Type Hinting 💡
    details: The utility functions and classes made in the project all have some form of type hinting if they aren't built in.
    link: https://docs.python.org/3/library/typing.html
  - title: DRF pagination 📃
    link: https://www.django-rest-framework.org/api-guide/pagination/
    details: For long responses. This project uses DRF pagination to avoid too much data egress that can cause bottlenecks as not all said data may be neede at once


---

