
export class Input {
  constructor() {
    this.keys = new Set();
    addEventListener('keydown', (e) => this.keys.add(e.code));
    addEventListener('keyup',   (e) => this.keys.delete(e.code));
  }
  down(code) { return this.keys.has(code); }
}
