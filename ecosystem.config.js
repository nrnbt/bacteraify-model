module.exports = {
  apps : [{
    name: 'bacteraify-web',
    script: 'start-app.sh',
    max_restarts: 5,
    interpreter: '/bin/bash',
    env: {
      NODE_ENV: 'production',
    }
  }],
};
