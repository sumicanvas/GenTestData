import { equalsFilter, noKeywordPipeline, runScenario } from "./common.js";

await runScenario({
  scenario: "news_mig 시나리오 2",
  description: "뉴스구분 조건만 사용해 해당 뉴스매체의 전체 뉴스를 최신순으로 조회합니다.",
  inputs: [{ key: "dgubun", label: "뉴스구분", example: "P" }],
  buildPipeline: ({ indexName, limit, dgubun }) =>
    noKeywordPipeline({ indexName, limit, filters: [equalsFilter("dgubun", dgubun)] }),
});
