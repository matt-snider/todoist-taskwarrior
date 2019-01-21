# TODO:
* [ ] Support `start`, `until` and `for`
    * Don't do within recur parsing, reparse whole string
    * https://get.todoist.help/hc/en-us/articles/360000636289
* [ ] Support repetition as regular period or offset from completion date (`every!`)
    * e.g. `every! 30 days` would be due 30 days after completion date
* [ ] Other 'every'
    * every 3rd friday
    * every 27th -- every 27th of the month (every 27 also works)
    * every jan 27th
    * every last day -- every last day of the month
* [ ] Delete todoist cache or add warning so user does not forget that potentially sensitive data is lying around in file system
* [ ] Handle inconsistencies (i.e. throw error or prompt for user input)
    * Taskwarrior: 'monthly' just means 30d (see: [link](https://github.com/GothenburgBitFactory/taskwarrior/issues/1647))
    * Taskwarrior: 'every monday,tuesday' is not possible

Testing:
* [ ] 'ev' as shortform for every
* [ ] For inconsistencies in meaning or support, an exception should be thrown

