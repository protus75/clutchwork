import { App, applyDocumentTheme, applyHostStyleVariables } from "@modelcontextprotocol/ext-apps";

export async function createDashboardApp(options = {}) {
  const app = new App({ name: "ClutchWork", version: "1.0.0" });
  const applyContext = (context) => {
    if (context?.theme) applyDocumentTheme(context.theme);
    if (context?.styles?.variables) applyHostStyleVariables(context.styles.variables);
  };
  app.ontoolinput = options.ontoolinput ?? (() => {});
  app.ontoolresult = options.ontoolresult ?? (() => {});
  app.onhostcontextchanged = (context) => {
    applyContext(context);
    options.onhostcontextchanged?.(context);
  };
  await app.connect();
  applyContext(app.getHostContext());
  return app;
}

if (typeof document !== "undefined" && !globalThis.__CLUTCH_DASHBOARD_NO_AUTOBOOT__) {
  createDashboardApp();
}
