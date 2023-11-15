const { spawn } = require('child_process');
const express = require('express');
const fs = require('fs');
const dotenv = require('dotenv');

const app = express();
const PORT = 3000;

dotenv.config();

// Function to install dependencies
function installDependencies(callback) {
  const installDeps = spawn('pip3', ['install', '-r', 'requirements.txt']);
  installDeps.stdout.on('data', (data) => console.log(`Dependencies Installation: ${data}`));
  installDeps.stderr.on('data', (data) => console.error(`Dependencies Installation Error: ${data}`));

  installDeps.on('close', (installCode) => {
    if (installCode === 0) {
      console.log('Dependencies installed successfully');
      callback();  // Call the provided callback function after successful installation
    } else {
      console.error(`Dependencies installation exited with code ${installCode}`);
    }
  });
}

// Function to run script1
function runScript1(res) {
  const script1 = spawn('python', ['script1.py']);
  script1.stdout.on('data', (data) => console.log(`Script 1: ${data}`));
  script1.stderr.on('data', (data) => console.error(`Script 1 Error: ${data}`));

  script1.on('close', (code) => {
    if (code === 0) {
      console.log('Script 1 executed successfully');
      // Check if res is defined before sending the response
      if (res && !res.headersSent) {
        res.send('Script 1 executed successfully');
      }
    } else {
      console.error(`Script 1 exited with code ${code}`);
      if (res && !res.headersSent) {
        res.status(500).json({ error: 'Script 1 Execution Error' });
      }
    }
  });
}

// Run the installation only once after starting the server
installDependencies(() => {
  console.log('Dependencies installation completed. Server is now starting.');

  // Run script1 when the server starts
  // runScript1();

  // Expose an endpoint to handle GET requests for /forecast
  app.get('/forecast', async (req, res) => {
    const child_id = req.query.child_id || 10006;
    const n_months = req.query.n_months || 2;

    // Run the Python script2 to forecast
    const script2 = spawn('python', ['script2.py', child_id, n_months]);

    let script2Output = '';
    let script2Error = '';

    script2.stdout.on('data', (data) => {
      script2Output += data.toString();
    });

    script2.stderr.on('data', (data) => {
      script2Error += data.toString();
    });

    script2.on('close', (code) => {
      if (code === 0) {
        try {
          // Read the JSON result from the file
          const resultFilePath = 'forecast_result.json';
          const resultData = fs.readFileSync(resultFilePath, 'utf8');

          // Send the raw output as part of the response
          res.send(resultData);
        } catch (error) {
          console.error(`Error parsing JSON: ${error}`);
          res.status(500).json({ error: 'Internal Server Error' });
        }
      } else {
        console.error(`Script 2 exited with code ${code}`);
        console.error(`Script 2 Error: ${script2Error}`);
        res.status(500).json({ error: 'Internal Server Error' });
      }
    });
  });

  app.get('/hardreload', (req, res) => {
    if (process.env.NODE_AUTH == req.query.auth && process.env.NODE_PASS == req.query.pass) runScript1(res);
    else {
      console.log("Unauthorized attempt to hard reload server!")
      res.status(401).send("You are not authenticated to hard reload the server!")
    }
  });

  app.listen(PORT, () => {
    console.log(`Server is running at http://localhost:${PORT}`);
  });
});
