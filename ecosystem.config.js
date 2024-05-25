module.exports = {
  apps : [{
    name: 'bacteraify-model',
    script: 'start-app.sh',
    max_restarts: 5,
    interpreter: '/bin/bash',
    env: {
      NODE_ENV: 'production',
    }
  }],
};
