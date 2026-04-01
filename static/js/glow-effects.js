/**
 * glow-effects.js
 *
 * Interactive Card Glow — freefrontend / Stripe-Technik
 * -------------------------------------------------------
 * Jede Karte mit der Klasse `.glow-card-inner` bekommt einen
 * CSS-Variablen-gesteuerten Spotlight-Effekt:
 *   --mouse-x / --mouse-y  → Position des Mauszeigers relativ zur Karte
 *
 * Das CSS-::before liest diese Werte und rendert einen
 * radial-gradient an exakt dieser Stelle (siehe theme.css).
 * Startwert -9999px hält den Gradient außerhalb des sichtbaren
 * Bereichs, bis die Maus die Karte betritt.
 */
(function initGlowCards() {
  'use strict';

  var OFFSCREEN = '-9999px';

  function attach(root) {
    var cards = root.querySelectorAll('.glow-card-inner');
    cards.forEach(function (card) {
      card.addEventListener('mousemove', function (e) {
        var rect = card.getBoundingClientRect();
        card.style.setProperty('--mouse-x', (e.clientX - rect.left) + 'px');
        card.style.setProperty('--mouse-y', (e.clientY - rect.top)  + 'px');
      });

      card.addEventListener('mouseleave', function () {
        card.style.setProperty('--mouse-x', OFFSCREEN);
        card.style.setProperty('--mouse-y', OFFSCREEN);
      });
    });
  }

  // Initialisierung: warten bis DOM bereit ist
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { attach(document); });
  } else {
    attach(document);
  }
}());
