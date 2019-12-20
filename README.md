# Sexy Knight
Discord bot for Sexy Knights guild.

Only works with birthdays for now.
Will announce a birthday in `#birthdays` at 12am GMT if one of the members has one.
Also possible to set a birthday for yourself with `$birthday 01.01` command, argument requires dd:mm format.

Requires `database.json` in the root folder to work with following format:

```json
{
  "members": [
    {
      "name": "member1",
      "id": 123456789012345678
    },
    {
      "name": "member2",
      "id": 098765432109876543,
      "birthday": "01.12"
    }
  ]
}
```
