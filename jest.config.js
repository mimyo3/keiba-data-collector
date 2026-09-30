module.exports = {
  testEnvironment: "node",
  testMatch: [
    "**/__tests__/**/*.(js|jsx)",
    "**/?(*.)+(spec|test).(js|jsx)"
  ],
  moduleFileExtensions: ["js", "jsx"],
  transform: {
    "^.+\\.(js|jsx)$": "babel-jest"
  }
};
