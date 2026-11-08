export function validateLogin(email: string, password: string): string | null {
  if (email.trim().length == 0) {
    return "Error: Please enter your email address.";
  }
  if (password.length == 0) {
    return "Error: Please enter your password.";
  }
  return null;
}

export function validateRegistration(
  email: string,
  password: string,
  passwordRepeat: string,
): string | null {
  if (email.trim().length == 0) {
    return "Error: Please enter your email address.";
  }
  if (password.length == 0) {
    return "Error: Please enter your password.";
  }

  if (passwordRepeat.length == 0) {
    return "Error: Please enter the password in password repeat field";
  }

  if (password != passwordRepeat) {
    return "Error: Passwords do not match.";
  }

  return null;
}
