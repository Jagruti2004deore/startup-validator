import { Component } from "react";

export class ErrorBoundary extends Component {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <div className="mx-auto max-w-md px-6 py-24 text-center">
        <h1 className="text-xl font-semibold tracking-tight">Something went wrong</h1>
        <p className="mt-2 text-sm text-muted">
          This page couldn&apos;t be shown. Your validations are safe.
        </p>
        <button
          type="button"
          onClick={() => window.location.assign("/")}
          className="mt-6 rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Back to Validate Idea
        </button>
      </div>
    );
  }
}