/* ==========================================================================
   WebAuthn / Passkeys Client Helper — Base64URL & Navigator Credentials API
   ========================================================================== */

const WebAuthnService = {
  /**
   * Checks if WebAuthn is supported on this browser.
   */
  isSupported() {
    return window.PublicKeyCredential !== undefined && typeof window.PublicKeyCredential === 'function';
  },

  /**
   * Converts a Base64URL string to an ArrayBuffer.
   */
  base64URLToBuffer(base64URLStr) {
    if (typeof base64URLStr !== 'string') return base64URLStr;
    
    // Add padding if required
    let base64 = base64URLStr.replace(/-/g, '+').replace(/_/g, '/');
    while (base64.length % 4 !== 0) {
      base64 += '=';
    }
    
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  },

  /**
   * Converts an ArrayBuffer to a Base64URL string.
   */
  bufferToBase64URL(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    const base64 = btoa(binary);
    return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
  },

  /**
   * Transforms raw WebAuthn JSON registration options into ArrayBuffers for navigator.credentials.create.
   */
  prepareRegistrationOptions(options) {
    const credOptions = JSON.parse(JSON.stringify(options));
    
    credOptions.challenge = this.base64URLToBuffer(credOptions.challenge);
    if (credOptions.user && credOptions.user.id) {
      credOptions.user.id = this.base64URLToBuffer(credOptions.user.id);
    }
    
    if (credOptions.excludeCredentials) {
      credOptions.excludeCredentials = credOptions.excludeCredentials.map(cred => ({
        ...cred,
        id: this.base64URLToBuffer(cred.id)
      }));
    }

    return credOptions;
  },

  /**
   * Transforms raw WebAuthn JSON authentication options into ArrayBuffers for navigator.credentials.get.
   */
  prepareAuthenticationOptions(options) {
    const authOptions = JSON.parse(JSON.stringify(options));
    
    authOptions.challenge = this.base64URLToBuffer(authOptions.challenge);
    
    if (authOptions.allowCredentials) {
      authOptions.allowCredentials = authOptions.allowCredentials.map(cred => ({
        ...cred,
        id: this.base64URLToBuffer(cred.id)
      }));
    }

    return authOptions;
  },

  /**
   * Triggers device biometric prompt for registration (navigator.credentials.create).
   */
  async registerPasskey(publicKeyOptions) {
    if (!this.isSupported()) {
      throw new Error("WebAuthn / Passkeys biometric feature is not supported on this device/browser.");
    }

    const preparedOptions = this.prepareRegistrationOptions(publicKeyOptions);
    const credential = await navigator.credentials.create({ publicKey: preparedOptions });
    
    if (!credential) {
      throw new Error("Biometric passkey creation was cancelled or failed.");
    }

    // Format response to send back to server
    return {
      id: credential.id,
      rawId: this.bufferToBase64URL(credential.rawId),
      type: credential.type,
      response: {
        attestationObject: this.bufferToBase64URL(credential.response.attestationObject),
        clientDataJSON: this.bufferToBase64URL(credential.response.clientDataJSON)
      },
      clientExtensionResults: credential.getClientExtensionResults()
    };
  },

  /**
   * Triggers device biometric prompt for authentication (navigator.credentials.get).
   */
  async authenticatePasskey(publicKeyOptions) {
    if (!this.isSupported()) {
      throw new Error("WebAuthn / Passkeys biometric feature is not supported on this device/browser.");
    }

    const preparedOptions = this.prepareAuthenticationOptions(publicKeyOptions);
    const credential = await navigator.credentials.get({ publicKey: preparedOptions });

    if (!credential) {
      throw new Error("Biometric authentication was cancelled or failed.");
    }

    // Format response to send back to server
    return {
      id: credential.id,
      rawId: this.bufferToBase64URL(credential.rawId),
      type: credential.type,
      response: {
        authenticatorData: this.bufferToBase64URL(credential.response.authenticatorData),
        clientDataJSON: this.bufferToBase64URL(credential.response.clientDataJSON),
        signature: this.bufferToBase64URL(credential.response.signature),
        userHandle: credential.response.userHandle ? this.bufferToBase64URL(credential.response.userHandle) : null
      },
      clientExtensionResults: credential.getClientExtensionResults()
    };
  }
};
