---
workflow: motion-graphics
flow: automation
storyboard: no
message: "Мешки корма для собак в наличии: Сириус, Трендлайн, Дилли, Пилот"
aspect: 1080x1920
language: ru
length: 10s
---

## Intent

Пример видео по сценарию «Вариант 2. Парад мешков» для заказчика (зоомагазин, Kaspi):
4 мешка по очереди падают в кадр на сильные доли бита, финал — все мешки вместе,
Яндекс Доставка, Kaspi Магазин и способы оплаты, призыв «Ссылка в профиле».

## Notes

- Inferred (not supplied yet): no product photos — bags are stylized placeholders in
  `assets/bag.js` (no brand packaging); no weights/prices; no store name or logo.
- Payment options (Kaspi Gold, Kaspi Red+, рассрочка) are typical Kaspi options — confirm
  with the client. Kaspi renamed Kaspi Red to Kaspi Red+ in August 2024; the Kaspi guide
  lists Kaspi Gold, Kaspi Red+, кредит, рассрочка, Kaspi Бонусы, сертификат and any
  Kazakhstani Visa/Mastercard for orders in Kaspi Магазин.
- Music: original synthesized 120 BPM beat, `assets/audio/make_beat.py`.
- CDNs are blocked here: GSAP and fonts (Unbounded, Rubik, Oswald; OFL) are vendored.
