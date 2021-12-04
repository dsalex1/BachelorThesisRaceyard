const express = require('express')
let { PythonShell } = require('python-shell')
const app = express()
const port = 3000

app.get('/', (req, res) => {

    PythonShell.run('main.py', {
        args: ["-b", req.query["b"], "-y", req.query["y"], "-f", req.query["f"]]
    }, function (err, results) {
        if (err) return res.status(500).send(err);
        // results is an array consisting of messages collected during execution
        res.send(results.join("\n"));
    });
})

app.listen(port, () => {
    console.log(`Example app listening at http://localhost:${port}`)
})