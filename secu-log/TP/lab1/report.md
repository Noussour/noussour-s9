# Practical Lab 1: Classical Ciphers

**Course:** Securite de Logiciel, USTHB  
**Student:** Benalia Mohamed, ID 31520920

## Objective

Practice three classical ciphers (Caesar, Playfair, Vigenere) with an online tool and check each result by hand.

**Tools used**

- CrypTool-Online (cryptool.org/en/cto) for Caesar and Vigenere.
- dCode (dcode.fr/playfair-cipher) for Playfair, because CrypTool-Online has no Playfair page.

**Notes**

- Digits are not part of the 26-letter alphabet, so the ciphers leave them out. Only the letters are encrypted.
- Spaces are removed from the messages before using the tools.
- In Playfair, J is merged with I.

---

## 1. Caesar cipher (key = 3)

Rule: each letter is moved 3 places forward in the alphabet to encrypt, and 3 places back to decrypt.

### a) Encrypt `benaliamohamed31520920`

| Plain | B | E | N | A | L | I | A | M | O | H | A | M | E | D |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Cipher | E | H | Q | D | O | L | D | P | R | K | D | P | H | G |

**Result: `EHQDOLDPRKDPHG`** (the digits `31520920` are ignored)

![Caesar encryption](screenshots/03-caesar-encrypt.jpg)

### b) Decrypt `dojhuld irrwedoo whdp lv qrw jrrg qrz`

Each letter is moved 3 places back: d to a, o to l, j to g, h to e, u to r, l to i, d to a, and so on.

**Result: `algeria football team is not good now`**

![Caesar decryption](screenshots/01-caesar-decrypt.jpg)

The manual result and the tool result are the same.

---

## 2. Playfair cipher

### Rules

1. Build a 5x5 grid: the key first (no repeated letters), then the rest of the alphabet. I and J share a cell.
2. Cut the message into pairs of letters. If a pair has twice the same letter, insert X between them.
3. Same row: take the letter on the right (to encrypt) or on the left (to decrypt).
4. Same column: take the letter below (to encrypt) or above (to decrypt).
5. Otherwise (rectangle): each letter is replaced by the one in its own row and in the column of the other letter.

### a) Encrypt `benaliamohamed` with the key `king`

Grid:

| K | I/J | N | G | A |
|---|---|---|---|---|
| B | C | D | E | F |
| H | L | M | O | P |
| Q | R | S | T | U |
| V | W | X | Y | Z |

Pairs: `BE NA LI AM OH AM ED`

| Pair | Case | Result |
|---|---|---|
| BE | same row | CF |
| NA | same row | GK |
| LI | same column | RC |
| AM | rectangle | NP |
| OH | same row | PL |
| AM | rectangle | NP |
| ED | same row | FE |

**Result: `CFGKRCNPPLNPFE`**

![Playfair grid in the tool](screenshots/04a-playfair-encrypt-grid.jpg)

![Playfair encryption result](screenshots/04b-playfair-encrypt-result.jpg)

### b) Decrypt `OMDXFNOMFQHUDLEK` with the key `sun`

Grid:

| S | U | N | A | B |
|---|---|---|---|---|
| C | D | E | F | G |
| H | I/J | K | L | M |
| O | P | Q | R | T |
| V | W | X | Y | Z |

Pairs: `OM DX FN OM FQ HU DL EK`, decrypted with the reverse rules (left and above):

| Pair | Case | Result |
|---|---|---|
| OM | rectangle | TH |
| DX | rectangle | EW |
| FN | rectangle | EA |
| OM | rectangle | TH |
| FQ | rectangle | ER |
| HU | rectangle | IS |
| DL | rectangle | FI |
| EK | rectangle | NE |

**Result: `THEWEATHERISFINE`**, that is "the weather is fine".

![Playfair decryption](screenshots/02-playfair-decrypt.jpg)

The manual result and the tool result are the same.

---

## 3. Vigenere cipher

### a) Encrypt `benaliamohamed31520920` with the key `usthb`

Rule: each letter is shifted by the matching letter of the key (A = 0, B = 1, ..., Z = 25). The key `USTHB` is repeated along the message.

| Plain | B | E | N | A | L | I | A | M | O | H | A | M | E | D |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Key | U | S | T | H | B | U | S | T | H | B | U | S | T | H |
| Shift | 20 | 18 | 19 | 7 | 1 | 20 | 18 | 19 | 7 | 1 | 20 | 18 | 19 | 7 |
| Cipher | V | W | G | H | M | C | S | F | V | I | U | E | X | K |

Example: B (1) + U (20) = 21 = V. N (13) + T (19) = 32, minus 26 = 6 = G.

**Result: `VWGHMCSFVIUEXK`** (the digits are ignored)

![Vigenere encryption](screenshots/05-vigenere-encrypt.jpg)

The manual result and the tool result are the same.

---

## Summary

| Task | Input | Key | Output |
|---|---|---|---|
| Caesar encrypt | benaliamohamed31520920 | 3 | EHQDOLDPRKDPHG |
| Caesar decrypt | dojhuld irrwedoo whdp lv qrw jrrg qrz | 3 | algeria football team is not good now |
| Playfair encrypt | benaliamohamed | king | CFGKRCNPPLNPFE |
| Playfair decrypt | OMDXFNOMFQHUDLEK | sun | THEWEATHERISFINE |
| Vigenere encrypt | benaliamohamed31520920 | usthb | VWGHMCSFVIUEXK |

In every case the manual calculation matches the tool output.
