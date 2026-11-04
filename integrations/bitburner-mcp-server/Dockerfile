FROM node:22-alpine AS build
ARG UPSTREAM_COMMIT=0229e9b93ea1ffc2a1e570561fc5102c6d19e29b
RUN apk add --no-cache git
WORKDIR /source
RUN git init && git remote add origin https://github.com/JoshuaGreeff/bitburner-mcp-server.git \
    && git fetch --depth=1 origin ${UPSTREAM_COMMIT} \
    && git checkout --detach FETCH_HEAD
COPY integrations/bitburner-mcp-server/package-lock.json ./package-lock.json
COPY integrations/bitburner-mcp-server/hardening.patch /tmp/hardening.patch
RUN git apply /tmp/hardening.patch \
    && npm ci --ignore-scripts \
    && npm run build \
    && npm prune --omit=dev \
    && npm audit --omit=dev

FROM node:22-alpine
ENV BB_API_HOST=127.0.0.1 \
    BB_API_PORT=3001 \
    BB_WS_HOST=127.0.0.1 \
    BB_WS_PORT=12525 \
    BB_DASHBOARD_HOST=127.0.0.1 \
    BB_DASHBOARD_PORT=3002
WORKDIR /srv
COPY --from=build --chown=node:node /source/dist ./dist
COPY --from=build --chown=node:node /source/public ./public
COPY --from=build --chown=node:node /source/node_modules ./node_modules
COPY --from=build --chown=node:node /source/package.json ./package.json
USER node
CMD ["node", "dist/api-server.js"]
