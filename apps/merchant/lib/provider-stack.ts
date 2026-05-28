import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as path from "node:path";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as nodejs from "aws-cdk-lib/aws-lambda-nodejs";
import * as apigwv2 from "aws-cdk-lib/aws-apigatewayv2";
import * as integrations from "aws-cdk-lib/aws-apigatewayv2-integrations";
import * as cloudfront from "aws-cdk-lib/aws-cloudfront";
import * as origins from "aws-cdk-lib/aws-cloudfront-origins";
import type { NetworkConfig } from "@x402-aws/shared";

export interface ProviderStackProps extends cdk.StackProps {
  network: NetworkConfig;
  recipientAddress: string;
  priceUsdc: string;
  cdpApiKeyId: string;
  cdpPrivateKey: string;
}

export class ProviderStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: ProviderStackProps) {
    super(scope, id, props);

    // Origin Lambda Returning Gated JSON
    const originFn = new nodejs.NodejsFunction(this, "OriginFn", {
      entry: path.join(__dirname, "origin-function/index.ts"),
      handler: "handler",
      runtime: lambda.Runtime.NODEJS_20_X,
      architecture: lambda.Architecture.ARM_64,
      memorySize: 256,
      timeout: cdk.Duration.seconds(5),
    });

    // HTTP API Gateway Routing GET Report To Origin Lambda
    const httpApi = new apigwv2.HttpApi(this, "OriginApi", {
      apiName: "x402-origin-api",
    });
    httpApi.addRoutes({
      path: "/report",
      methods: [apigwv2.HttpMethod.GET],
      integration: new integrations.HttpLambdaIntegration("OriginIntegration", originFn),
    });

    // Edge Config Inlined Into Lambda Edge Bundle At Synth
    const edgeConfig = {
      caip2: props.network.caip2,
      usdc: props.network.usdc,
      recipientAddress: props.recipientAddress,
      priceUsdc: props.priceUsdc,
      cdpFacilitatorUrl: props.network.cdpFacilitatorUrl,
      cdpApiKeyId: props.cdpApiKeyId,
      cdpPrivateKey: props.cdpPrivateKey,
    };

    // Lambda Edge Function On Viewer Request
    const edgeFn = new nodejs.NodejsFunction(this, "EdgeFn", {
      entry: path.join(__dirname, "edge-function/index.ts"),
      handler: "handler",
      runtime: lambda.Runtime.NODEJS_20_X,
      architecture: lambda.Architecture.X86_64,
      memorySize: 128,
      timeout: cdk.Duration.seconds(5),
      bundling: {
        minify: true,
        target: "node20",
        define: {
          __EDGE_CONFIG__: JSON.stringify(edgeConfig),
        },
      },
    });

    // CloudFront Origin Pointing At HTTP API
    const apiOrigin = new origins.HttpOrigin(
      `${httpApi.apiId}.execute-api.${this.region}.amazonaws.com`,
      {
        protocolPolicy: cloudfront.OriginProtocolPolicy.HTTPS_ONLY,
      }
    );

    // CloudFront Distribution Wired To Edge Function
    const distribution = new cloudfront.Distribution(this, "Cdn", {
      defaultBehavior: {
        origin: apiOrigin,
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
        // Must NOT forward the viewer Host header: the API Gateway execute-api origin
        // rejects requests whose Host doesn't match its own domain with 403 Forbidden.
        originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
        edgeLambdas: [
          {
            functionVersion: edgeFn.currentVersion,
            eventType: cloudfront.LambdaEdgeEventType.VIEWER_REQUEST,
          },
        ],
        allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
      },
    });

    // Stack Outputs
    new cdk.CfnOutput(this, "DistributionDomainName", {
      value: distribution.distributionDomainName,
      description: "Public CloudFront URL the agent hits",
    });
    new cdk.CfnOutput(this, "OriginApiEndpoint", {
      value: httpApi.apiEndpoint,
      description: "API Gateway endpoint for direct testing",
    });
    new cdk.CfnOutput(this, "EdgeFunctionArn", {
      value: edgeFn.currentVersion.functionArn,
      description: "Lambda Edge function ARN with version",
    });
  }
}
