import { equalsFilter, noKeywordPipeline, runScenario } from "./common.js";

await runScenario({
  scenario: "news_mig_500 시나리오 5",
  description: "종목코드 조건만 사용해 해당 종목의 전체 뉴스를 최신순으로 조회합니다.",
  inputs: [{ key: "shcode", label: "종목코드", example: "005930" }],
  buildPipeline: ({ indexName, limit, shcode, shcodePath }) =>
    noKeywordPipeline({
      indexName,
      limit,
      filters: [equalsFilter(shcodePath, shcode)],
    }),
});
