import { fuzzyPipeline, runScenario } from "./common.js";

await runScenario({
  scenario: "news_mig 시나리오 9",
  description: "Fuzzy 검색입니다. title과 contents를 모두 should로 검색합니다.",
  inputs: [{ key: "query", label: "검색어", example: "삼영전자" }],
  buildPipeline: ({ indexName, limit, query, args }) =>
    fuzzyPipeline({
      indexName,
      limit,
      query,
      titleBoost: args["title-boost"] ? Number(args["title-boost"]) : 5,
      contentsBoost: args["contents-boost"] ? Number(args["contents-boost"]) : 1,
      minScore: args["min-score"] !== undefined ? Number(args["min-score"]) : 1,
    }),
});
